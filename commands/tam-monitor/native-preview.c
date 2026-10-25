#define _GNU_SOURCE
#include "native-preview.h"
#include "native-events.h"
#include <tam_display.h>
#include <tam_display_session.h>
#include <tam_vt.h>
#include <errno.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/signalfd.h>
#include <sys/socket.h>
#include <sys/timerfd.h>
#include <sys/wait.h>
#include <unistd.h>

/* The UI never owns KMS. Its separate session/process-group recovery worker
 * observes logind and owns the DRM description and retained state for this bounded trial.
 * Closing the private socket (including UI SIGKILL) initiates restoration.
 * No state file, untrusted serialized snapshot or permanent service. */
struct report { int ready, code, syserr; char message[160]; };

static bool send_report(int fd, bool ready, const struct tam_display_error *e)
{
    struct report r = {.ready = ready, .code = e->code, .syserr = e->system_errno};
    snprintf(r.message, sizeof(r.message), "%s", e->message);
    return send(fd, &r, sizeof(r), MSG_NOSIGNAL) == sizeof(r);
}

static void close_inherited(int a, int b)
{
    unsigned first = a < b ? (unsigned)a : (unsigned)b;
    unsigned last = a < b ? (unsigned)b : (unsigned)a;
    if (first > 3) close_range(3, first - 1, 0);
    if (last > first + 1) close_range(first + 1, last - 1, 0);
    close_range(last + 1, UINT_MAX, 0);
}

struct access {
    struct tam_display_session *session;
    const struct tam_vt *vt;
    int control, timer, signals, hotplug;
};
static enum tam_display_result check_access(void *context, bool restoring, struct tam_display_error *e)
{
    struct access *a = context;
    if (!restoring) {
        struct pollfd fds[] = {{a->control, POLLIN, 0}, {a->timer, POLLIN, 0}, {a->signals, POLLIN, 0}};
        if (poll(fds, 3, 0) < 0 || fds[0].revents || fds[1].revents || fds[2].revents) {
            e->code = TAM_DISPLAY_INACTIVE;
            strcpy(e->message, "Preview owner, signal or deadline ended before commit"); return e->code;
        }
        if (tam_monitor_hotplug_event(a->hotplug)) {
            e->code = TAM_DISPLAY_STALE;
            strcpy(e->message, "Display hotplug occurred before commit"); return e->code;
        }
        return tam_display_session_check(a->session, e);
    }
    return tam_display_session_check_restore(a->session, e);
}

static void worker(int control, struct tam_vt vt, unsigned card, const char *keep,
    unsigned seconds, const sigset_t *mask)
{
    struct tam_display_error e = {0}, restore = {0};
    struct tam_display_session *session = NULL;
    struct tam_display_state *state = NULL;
    int timer = -1, signals = -1, hotplug = -1;
    bool attempted = false;
    if (setpgid(0, 0) < 0) { e.code = TAM_DISPLAY_IO; e.system_errno = errno; strcpy(e.message, "Cannot isolate recovery process group"); goto done; }
    close_inherited(control, vt.fd);
    signals = signalfd(-1, mask, SFD_CLOEXEC | SFD_NONBLOCK);
    timer = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
    if (signals < 0 || timer < 0) { e.code = TAM_DISPLAY_IO; e.system_errno = errno; strcpy(e.message, "Cannot arm independent recovery events"); goto done; }
    /* Deadline includes acquisition/preparation, rather than starting after an
     * experimental write. A stopped UI cannot postpone it. */
    struct itimerspec deadline = {.it_value = {.tv_sec = seconds}};
    if (timerfd_settime(timer, 0, &deadline, NULL) < 0) { e.code = TAM_DISPLAY_IO; e.system_errno = errno; strcpy(e.message, "Cannot arm recovery deadline"); goto done; }
    if (tam_vt_claim(&vt, &e)) goto done;
    hotplug = tam_monitor_hotplug_open();
    if (hotplug < 0) { e.code = TAM_DISPLAY_IO; e.system_errno = errno; strcpy(e.message, "Cannot watch display hotplug events"); goto done; }
    if (tam_display_session_open(&vt, card, &session, &e)) goto done;
    if (tam_display_capture_fd(tam_display_session_device(session), &state, &e)) goto done;
    struct access access = {session, &vt, control, timer, signals, hotplug};
    tam_display_state_set_access_check(state, check_access, &access);
    struct pollfd ready[] = {{control, POLLIN, 0}, {timer, POLLIN, 0}, {signals, POLLIN, 0}};
    /* UI readiness handshake makes owner liveness a precondition for the write. */
    if (!send_report(control, true, &e)) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Recovery readiness channel failed"); goto done;
    }
    if (poll(ready, 3, 2000) <= 0 || !(ready[0].revents & POLLIN) || ready[1].revents || ready[2].revents) {
        e.code = TAM_DISPLAY_INACTIVE; strcpy(e.message, "Preview ended before the display write"); goto done;
    }
    char go = 0;
    if (recv(control, &go, 1, 0) != 1 || go != 'G') {
        e.code = TAM_DISPLAY_INACTIVE; strcpy(e.message, "Preview owner ended before the display write"); goto done;
    }
    if (tam_display_session_check(session, &e)) goto done;
    /* No pending death/signal/expiry is allowed between preparation and apply. */
    if (poll(ready, 3, 0) < 0 || ready[0].revents || ready[1].revents || ready[2].revents) {
        e.code = TAM_DISPLAY_INACTIVE; strcpy(e.message, "Preview cancelled before the display write"); goto done;
    }
    if (tam_monitor_hotplug_event(hotplug)) {
        e.code = TAM_DISPLAY_STALE; strcpy(e.message, "Display hotplug occurred during preparation"); goto done;
    }
    attempted = true;
    if (tam_display_state_keep(state, keep, &e)) goto recover;
    for (;;) {
        enum tam_display_session_event event = tam_display_session_dispatch(session);
        if (event != TAM_DISPLAY_SESSION_RUNNING) break;
        struct pollfd fds[] = {{control, POLLIN, 0}, {timer, POLLIN, 0}, {signals, POLLIN, 0},
            {tam_display_session_bus_fd(session), (short)tam_display_session_bus_events(session), 0},
            {hotplug, POLLIN, 0}};
        int n = poll(fds, 5, -1);
        if (n < 0) { if (errno == EINTR) continue; e.code = TAM_DISPLAY_IO; e.system_errno = errno; break; }
        if (fds[0].revents || fds[1].revents || fds[2].revents) break;
        if (fds[4].revents && tam_monitor_hotplug_event(hotplug)) {
            e.code = TAM_DISPLAY_STALE; strcpy(e.message, "Display hotplug ends this bounded selection"); break;
        }
        /* Bus readiness is drained on the next iteration; no periodic redraw,
         * polling or output reapplication. Resume ends the old lifetime. */
    }
recover:
    if (state && attempted) {
        enum tam_display_session_event event = tam_display_session_dispatch(session);
        if (event == TAM_DISPLAY_SESSION_LOST) {
            restore.code = TAM_DISPLAY_RESTORE_FAILED;
            strcpy(restore.message, "Device/session was revoked; no stale restoration was replayed");
        } else if (!tam_display_session_check_restore(session, &restore)) {
            tam_display_state_restore(state, &restore);
        } else {
            restore.code = TAM_DISPLAY_RESTORE_FAILED;
        }
        if (restore.code) e = restore;
    }
done:
    tam_display_state_free(state);
    tam_display_session_close(session);
    bool handoff = false;
    if (signals >= 0) {
        struct signalfd_siginfo received;
        for (int i = 0; i < 32 && read(signals, &received, sizeof(received)) == sizeof(received); ++i)
            if (received.ssi_signo == SIGUSR1) handoff = true;
    }
    restore = (struct tam_display_error){0};
    if (tam_vt_release(&vt, handoff, &restore)) e = restore;
    if (hotplug >= 0) close(hotplug);
    if (timer >= 0) close(timer);
    if (signals >= 0) close(signals);
    tam_vt_close(&vt);
    send_report(control, false, &e);
    close(control);
    _exit(e.code ? 1 : 0);
}

int tam_monitor_preview(unsigned card, const char *keep, unsigned seconds, int json)
{
    struct tam_display_error e = {0};
    struct tam_vt vt = {.fd = -1};
    int control[2] = {-1, -1}, status = 0;
    pid_t child = -1;
    sigset_t mask, oldmask;
    sigemptyset(&mask);
    const int caught[] = {SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGTSTP, SIGTTIN, SIGTTOU, SIGUSR1, SIGUSR2};
    for (size_t i = 0; i < sizeof(caught)/sizeof(*caught); ++i) sigaddset(&mask, caught[i]);
    if (tam_vt_open(&vt, &e)) goto finish;
    if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, control) < 0 ||
        sigprocmask(SIG_BLOCK, &mask, &oldmask) < 0) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno; strcpy(e.message, "Cannot prepare recovery channel"); goto finish;
    }
    child = fork();
    if (!child) { close(control[0]); worker(control[1], vt, card, keep, seconds, &mask); }
    if (child < 0) { e.code = TAM_DISPLAY_IO; e.system_errno = errno; strcpy(e.message, "Cannot start recovery guard"); }
    close(control[1]); control[1] = -1;
    tam_vt_close(&vt);
    if (child > 0) {
        int signals = signalfd(-1, &mask, SFD_CLOEXEC | SFD_NONBLOCK);
        struct pollfd fds[] = {{control[0], POLLIN, 0}, {signals, POLLIN, 0}};
        if (signals < 0) shutdown(control[0], SHUT_WR);
        bool ready = false, complete = false;
        for (;;) {
            int n = poll(fds, 2, (int)(seconds + 10) * 1000);
            if (n < 0 && errno == EINTR) continue;
            if (n <= 0 || fds[1].revents) {
                /* Closing the UI channel requests restore. SIGCONT lets a
                 * stopped guard consume it; never SIGKILL a recovery owner. */
                shutdown(control[0], SHUT_WR);
                kill(child, SIGCONT);
            }
            if (fds[0].revents & POLLIN) {
                struct report r;
                ssize_t got = recv(control[0], &r, sizeof(r), 0);
                if (got == sizeof(r)) {
                    e.code = r.code; e.system_errno = r.syserr;
                    memcpy(e.message, r.message, sizeof(e.message)); e.message[sizeof(e.message)-1] = 0;
                    if (r.ready && !ready && !e.code) {
                        ready = true;
                        char go = 'G';
                        if (send(control[0], &go, 1, MSG_NOSIGNAL) != 1) shutdown(control[0], SHUT_WR);
                    } else { complete = true; break; }
                } else break;
            }
            if (!(fds[0].revents & POLLIN) && (fds[0].revents & (POLLHUP | POLLERR | POLLNVAL))) break;
            if (n <= 0 || fds[1].revents) {
                /* Continue receiving the bounded worker's restoration report. */
                if (signals >= 0) { close(signals); signals = -1; fds[1].fd = -1; }
                fds[1].revents = 0;
            }
        }
        if (signals >= 0) close(signals);
        while (waitpid(child, &status, 0) < 0 && errno == EINTR) {}
        if (!complete || !WIFEXITED(status) || WEXITSTATUS(status)) {
            if (!e.code) { e.code = TAM_DISPLAY_RESTORE_FAILED; strcpy(e.message, "Recovery guard failed; kernel fallback is unproven"); }
        }
    }
    /* Drain consumed UI cancellation signals before restoring the caller mask. */
    struct timespec zero = {0};
    while (sigtimedwait(&mask, NULL, &zero) >= 0) {}
    sigprocmask(SIG_SETMASK, &oldmask, NULL);
finish:
    tam_vt_close(&vt);
    for (int i = 0; i < 2; ++i) if (control[i] >= 0) close(control[i]);
    if (json) printf("{\"ok\":%s,\"code\":%d,\"errno\":%d,\"physical_proof\":false}\n", e.code ? "false" : "true", e.code, e.system_errno);
    if (e.code) fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", e.message, e.code, e.system_errno);
    else if (!json) puts("Bounded display trial restored and released; physical fbcon/standby proof remains separate.");
    return e.code ? 1 : 0;
}
