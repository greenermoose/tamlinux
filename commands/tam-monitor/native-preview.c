#define _GNU_SOURCE
#include "native-preview.h"
#include "native-events.h"
#include "native-hw.h"
#include <tam_display.h>
#include <tam_display_session.h>
#include <tam_vt.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/signalfd.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/timerfd.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* The UI never owns KMS. Its separate session/process-group recovery worker
 * observes logind and owns the DRM description and retained state.
 * Closing the private socket (including UI/shell SIGKILL) initiates restoration.
 * No state file, untrusted serialized snapshot or permanent service. */
struct report { int ready, code, syserr; char message[160]; };

static void quoted_json(const char *s)
{
    putchar('"');
    for (; s && *s; ++s) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') { putchar('\\'); putchar(c); }
        else if (c < 32 || c > 126) printf("\\u%04x", c);
        else putchar(c);
    }
    putchar('"');
}

static bool send_report(int fd, int ready, const struct tam_display_error *e)
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
    bool interactive_client;
};

static enum tam_display_result check_access(void *context, bool restoring, struct tam_display_error *e)
{
    struct access *a = context;
    if (!restoring) {
        struct pollfd fds[] = {
            {a->control, POLLIN, 0},
            {a->timer, POLLIN, 0},
            {a->signals, POLLIN, 0}
        };
        if (poll(fds, 3, 0) < 0 || fds[0].revents ||
            (a->timer >= 0 && fds[1].revents) || fds[2].revents) {
            e->code = TAM_DISPLAY_INACTIVE;
            strcpy(e->message, "Preview owner, signal or deadline ended before commit");
            return e->code;
        }
        if (tam_monitor_hotplug_event(a->hotplug)) {
            e->code = TAM_DISPLAY_STALE;
            strcpy(e->message, "Display hotplug occurred before commit");
            return e->code;
        }
        return a->interactive_client
            ? tam_display_session_check_restore(a->session, e)
            : tam_display_session_check(a->session, e);
    }
    return tam_display_session_check_restore(a->session, e);
}

static bool supervisor_socket_path(unsigned vt_number, char *out, size_t cap, bool create_dir)
{
    if (!out || cap < 64) return false;
    char dir[256] = {0};
    const char *override_dir = getenv("TAM_MONITOR_RUNTIME_DIR");
    const char *xdg = getenv("XDG_RUNTIME_DIR");
    uid_t uid = getuid();
    if (override_dir && *override_dir == '/' && strlen(override_dir) < 180) {
        snprintf(dir, sizeof(dir), "%s", override_dir);
    } else if (xdg && *xdg == '/' && strlen(xdg) < 180) {
        struct stat st;
        if (lstat(xdg, &st) == 0 && S_ISDIR(st.st_mode) && st.st_uid == uid && (st.st_mode & 0077) == 0)
            snprintf(dir, sizeof(dir), "%s/tam-monitor", xdg);
    }
    if (!dir[0])
        snprintf(dir, sizeof(dir), "/tmp/tam-monitor-%u", (unsigned)uid);
    if (create_dir) {
        (void)mkdir(dir, 0700);
    }
    struct stat st;
    if (lstat(dir, &st) < 0 || !S_ISDIR(st.st_mode) || st.st_uid != uid || (st.st_mode & 0077) != 0)
        return false;
    int n = snprintf(out, cap, "%s/vt%u.sock", dir, vt_number);
    return n > 0 && (size_t)n < cap;
}

static int open_supervisor_listener(unsigned vt_number, char *sock_path, size_t path_cap)
{
    if (!supervisor_socket_path(vt_number, sock_path, path_cap, true)) {
        sock_path[0] = 0;
        return -1;
    }
    struct sockaddr_un addr = {.sun_family = AF_UNIX};
    if (strlen(sock_path) >= sizeof(addr.sun_path)) {
        sock_path[0] = 0;
        return -1;
    }
    snprintf(addr.sun_path, sizeof(addr.sun_path), "%s", sock_path);
    unlink(sock_path);
    int fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
    if (fd < 0) { sock_path[0] = 0; return -1; }
    mode_t old_umask = umask(0077);
    int rc = bind(fd, (struct sockaddr *)&addr, sizeof(addr));
    umask(old_umask);
    if (rc < 0 || listen(fd, 4) < 0) {
        close(fd);
        unlink(sock_path);
        sock_path[0] = 0;
        return -1;
    }
    return fd;
}

int tam_monitor_supervisor_request(unsigned vt_number, const char *request,
    struct tam_display_error *e)
{
    if (e) memset(e, 0, sizeof(*e));
    char sock_path[256] = {0};
    if (!supervisor_socket_path(vt_number, sock_path, sizeof(sock_path), false))
        return -1;
    struct sockaddr_un addr = {.sun_family = AF_UNIX};
    if (strlen(sock_path) >= sizeof(addr.sun_path)) return -1;
    snprintf(addr.sun_path, sizeof(addr.sun_path), "%s", sock_path);
    int fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    if (fd < 0) return -1;
    struct timeval tv = {.tv_sec = 4, .tv_usec = 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(fd);
        return -1;
    }
    struct ucred cred = {0};
    socklen_t clen = sizeof(cred);
    if (getsockopt(fd, SOL_SOCKET, SO_PEERCRED, &cred, &clen) < 0 || cred.uid != getuid()) {
        close(fd);
        return -1;
    }
    size_t len = strlen(request);
    if (send(fd, request, len, MSG_NOSIGNAL) != (ssize_t)len) {
        close(fd);
        if (e) { e->code = TAM_DISPLAY_IO; e->system_errno = errno; strcpy(e->message, "Cannot send request to active monitor supervisor"); }
        return 1;
    }
    struct report r = {0};
    ssize_t got = recv(fd, &r, sizeof(r), 0);
    close(fd);
    if (got != sizeof(r)) {
        if (e) { e->code = TAM_DISPLAY_IO; e->system_errno = errno; strcpy(e->message, "Active monitor supervisor did not respond"); }
        return 1;
    }
    if (e) {
        e->code = r.code;
        e->system_errno = r.syserr;
        snprintf(e->message, sizeof(e->message), "%s", r.message);
    }
    return r.code ? 1 : 0;
}

static bool handle_client_request(int listen_fd, struct tam_display_state *state,
    struct access *access, struct tam_display_error *session_err)
{
    int cfd = accept4(listen_fd, NULL, NULL, SOCK_CLOEXEC);
    if (cfd < 0) return false;
    struct timeval tv = {.tv_sec = 2, .tv_usec = 0};
    setsockopt(cfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(cfd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    struct ucred cred = {0};
    socklen_t clen = sizeof(cred);
    struct tam_display_error reply = {0};
    bool stop_session = false;
    if (getsockopt(cfd, SOL_SOCKET, SO_PEERCRED, &cred, &clen) < 0 || cred.uid != getuid()) {
        reply.code = TAM_DISPLAY_PERMISSION;
        strcpy(reply.message, "Supervisor client UID mismatch");
        send_report(cfd, 0, &reply);
        close(cfd);
        return false;
    }
    char buf[512];
    ssize_t n = recv(cfd, buf, sizeof(buf) - 1, 0);
    if (n <= 0) { close(cfd); return false; }
    buf[n] = 0;
    access->interactive_client = true;
    if (!strncmp(buf, "WAKE ", 5)) {
        tam_display_state_wake(state, buf + 5, &reply);
    } else if (!strncmp(buf, "BLANK ", 6)) {
        const char *names[TAM_DISPLAY_MAX_OBJECTS];
        size_t count = 0;
        char *save = NULL;
        for (char *tok = strtok_r(buf + 6, "\n", &save); tok && count < TAM_DISPLAY_MAX_OBJECTS;
             tok = strtok_r(NULL, "\n", &save)) {
            if (*tok) names[count++] = tok;
        }
        tam_display_state_blank(state, names, count, &reply);
    } else if (!strncmp(buf, "KEEP ", 5)) {
        tam_display_state_keep(state, buf + 5, &reply);
    } else if (!strcmp(buf, "RESTORE")) {
        tam_display_state_restore(state, &reply);
    } else if (!strcmp(buf, "STOP")) {
        tam_display_state_restore(state, &reply);
        if (reply.code && session_err) *session_err = reply;
        stop_session = true;
    } else {
        reply.code = TAM_DISPLAY_INVALID;
        strcpy(reply.message, "Unknown supervisor request");
    }
    access->interactive_client = false;
    send_report(cfd, 0, &reply);
    close(cfd);
    return stop_session;
}

enum worker_mode {
    MODE_PREVIEW,
    MODE_KEEP,
    MODE_BLANK
};

struct worker_args {
    enum worker_mode mode;
    unsigned card;
    const char *keep;
    const char *const *blank_connectors;
    size_t blank_count;
    unsigned seconds;
    bool verify_cfb;
    struct tam_console_fb cfb;
    bool enable_socket;
};

static void worker(int control, struct tam_vt vt, const struct worker_args *w,
    const sigset_t *mask)
{
    struct tam_display_error e = {0}, restore = {0};
    struct tam_display_session *session = NULL;
    struct tam_display_state *state = NULL;
    int timer = -1, signals = -1, hotplug = -1, listen_fd = -1;
    char sock_path[256] = {0};
    bool attempted = false;
    if (setpgid(0, 0) < 0) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Cannot isolate recovery process group");
        goto done;
    }
    close_inherited(control, vt.fd);
    signals = signalfd(-1, mask, SFD_CLOEXEC | SFD_NONBLOCK);
    if (signals < 0) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Cannot arm independent recovery events");
        goto done;
    }
    if (w->seconds > 0) {
        timer = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
        if (timer < 0) {
            e.code = TAM_DISPLAY_IO; e.system_errno = errno;
            strcpy(e.message, "Cannot arm independent recovery events");
            goto done;
        }
        /* Deadline includes acquisition/preparation, rather than starting after an
         * experimental write. A stopped UI cannot postpone it. */
        struct itimerspec deadline = {.it_value = {.tv_sec = w->seconds}};
        if (timerfd_settime(timer, 0, &deadline, NULL) < 0) {
            e.code = TAM_DISPLAY_IO; e.system_errno = errno;
            strcpy(e.message, "Cannot arm recovery deadline");
            goto done;
        }
    }
    if (tam_vt_claim(&vt, &e)) goto done;
    hotplug = tam_monitor_hotplug_open();
    if (hotplug < 0) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Cannot watch display hotplug events");
        goto done;
    }
    if (tam_display_session_open(&vt, w->card, &session, &e)) goto done;
    if (tam_display_capture_fd(tam_display_session_device(session), &state, &e)) goto done;
    if (w->verify_cfb) {
        struct tam_console_fb cfb = w->cfb;
        if (tam_display_state_verify_console_fb(state, &cfb, &e)) goto done;
    }
    struct access access = {session, &vt, control, timer, signals, hotplug, false};
    tam_display_state_set_access_check(state, check_access, &access);
    struct pollfd ready[] = {{control, POLLIN, 0}, {timer, POLLIN, 0}, {signals, POLLIN, 0}};
    /* UI readiness handshake makes owner liveness a precondition for the write. */
    if (!send_report(control, 1, &e)) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Recovery readiness channel failed");
        goto done;
    }
    if (poll(ready, 3, 2000) <= 0 || !(ready[0].revents & POLLIN) ||
        (timer >= 0 && ready[1].revents) || ready[2].revents) {
        e.code = TAM_DISPLAY_INACTIVE;
        strcpy(e.message, "Preview ended before the display write");
        goto done;
    }
    char go = 0;
    if (recv(control, &go, 1, 0) != 1 || go != 'G') {
        e.code = TAM_DISPLAY_INACTIVE;
        strcpy(e.message, "Preview owner ended before the display write");
        goto done;
    }
    if (tam_display_session_check(session, &e)) goto done;
    /* No pending death/signal/expiry is allowed between preparation and apply. */
    if (poll(ready, 3, 0) < 0 || ready[0].revents ||
        (timer >= 0 && ready[1].revents) || ready[2].revents) {
        e.code = TAM_DISPLAY_INACTIVE;
        strcpy(e.message, "Preview cancelled before the display write");
        goto done;
    }
    if (tam_monitor_hotplug_event(hotplug)) {
        e.code = TAM_DISPLAY_STALE;
        strcpy(e.message, "Display hotplug occurred during preparation");
        goto done;
    }
    attempted = true;
    if (w->mode == MODE_BLANK) {
        if (tam_display_state_blank(state, w->blank_connectors, w->blank_count, &e)) goto recover;
    } else {
        if (tam_display_state_keep(state, w->keep, &e)) goto recover;
    }
    if (w->enable_socket) {
        listen_fd = open_supervisor_listener(vt.number, sock_path, sizeof(sock_path));
        if (!send_report(control, 2, &e)) goto recover;
    }
    for (;;) {
        enum tam_display_session_event event = tam_display_session_dispatch(session);
        if (event != TAM_DISPLAY_SESSION_RUNNING) break;
        struct pollfd fds[] = {
            {control, POLLIN, 0},
            {timer, POLLIN, 0},
            {signals, POLLIN, 0},
            {tam_display_session_bus_fd(session), (short)tam_display_session_bus_events(session), 0},
            {hotplug, POLLIN, 0},
            {listen_fd, POLLIN, 0}
        };
        int n = poll(fds, 6, -1);
        if (n < 0) {
            if (errno == EINTR) continue;
            e.code = TAM_DISPLAY_IO; e.system_errno = errno;
            break;
        }
        if (fds[0].revents || (timer >= 0 && fds[1].revents) || fds[2].revents) break;
        if (fds[4].revents && tam_monitor_hotplug_event(hotplug)) {
            e.code = TAM_DISPLAY_STALE;
            strcpy(e.message, "Display hotplug ends this bounded selection");
            break;
        }
        if (listen_fd >= 0 && (fds[5].revents & POLLIN)) {
            if (handle_client_request(listen_fd, state, &access, &e)) break;
        }
    }
recover:
    if (listen_fd >= 0) {
        close(listen_fd);
        listen_fd = -1;
        if (sock_path[0]) unlink(sock_path);
    }
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
    if (listen_fd >= 0) {
        close(listen_fd);
        if (sock_path[0]) unlink(sock_path);
    }
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
    send_report(control, 0, &e);
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
    struct worker_args w = {
        .mode = MODE_PREVIEW,
        .card = card,
        .keep = keep,
        .seconds = seconds,
        .verify_cfb = false,
        .enable_socket = false
    };
    child = fork();
    if (!child) { close(control[0]); worker(control[1], vt, &w, &mask); }
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

static bool extract_card_prefix(const char *name, unsigned *card_out)
{
    if (!name || strncmp(name, "card", 4) != 0 || !isdigit((unsigned char)name[4]))
        return false;
    const char *p = name + 4;
    unsigned long c = 0;
    while (isdigit((unsigned char)*p)) {
        c = c * 10 + (unsigned)(*p - '0');
        if (c >= 64) return false;
        ++p;
    }
    if (*p != '-' || !p[1]) return false;
    *card_out = (unsigned)c;
    return true;
}

static enum tam_display_result set_err(struct tam_display_error *e,
    enum tam_display_result code, int syserr, const char *msg)
{
    if (e) {
        e->code = code;
        e->system_errno = syserr;
        snprintf(e->message, sizeof(e->message), "%s", msg);
    }
    return code;
}

static enum tam_display_result resolve_target_card(unsigned vt_number,
    unsigned explicit_card, const char *first_connector,
    unsigned *card_out, bool *have_cfb_out, struct tam_console_fb *cfb_out,
    struct tam_display_error *e)
{
    *have_cfb_out = false;
    memset(cfb_out, 0, sizeof(*cfb_out));
    unsigned prefix_card = 64;
    bool has_prefix = extract_card_prefix(first_connector, &prefix_card);
    if (explicit_card < 64 && has_prefix && explicit_card != prefix_card) {
        return set_err(e, TAM_DISPLAY_INVALID, 0,
            "Connector card prefix does not match --card");
    }
    struct tam_display_error map_err = {0};
    if (tam_display_map_console_fb(vt_number, cfb_out, &map_err) == TAM_DISPLAY_OK) {
        *have_cfb_out = true;
        if (explicit_card < 64 && explicit_card != cfb_out->card)
            return set_err(e, TAM_DISPLAY_UNSUPPORTED, 0,
                "Requested DRM card does not back this VT's framebuffer console");
        if (has_prefix && prefix_card != cfb_out->card)
            return set_err(e, TAM_DISPLAY_UNSUPPORTED, 0,
                "Selected connector is not on this VT's console DRM card");
        *card_out = cfb_out->card;
        return TAM_DISPLAY_OK;
    }
    if (explicit_card < 64) {
        *card_out = explicit_card;
        return TAM_DISPLAY_OK;
    }
    if (has_prefix) {
        *card_out = prefix_card;
        return TAM_DISPLAY_OK;
    }
    *e = map_err;
    return map_err.code ? map_err.code : TAM_DISPLAY_UNSUPPORTED;
}

static int run_supervised_session(const struct worker_args *w_template,
    bool spawn_shell, int json)
{
    struct tam_display_error e = {0};
    struct tam_vt vt = {.fd = -1};
    int control[2] = {-1, -1}, status = 0, shell_exit = 0;
    pid_t child = -1, shell_pid = -1;
    sigset_t mask, oldmask;
    sigemptyset(&mask);
    const int caught[] = {SIGINT, SIGTERM, SIGHUP, SIGQUIT, SIGTSTP, SIGTTIN, SIGTTOU, SIGUSR1, SIGUSR2, SIGCHLD};
    for (size_t i = 0; i < sizeof(caught)/sizeof(*caught); ++i) sigaddset(&mask, caught[i]);
    if (tam_vt_open(&vt, &e)) goto finish;

    /* If not starting a new shell or bounded timer, check for an active supervisor on this VT. */
    if (!spawn_shell && w_template->seconds == 0) {
        char req[256];
        if (w_template->mode == MODE_KEEP)
            snprintf(req, sizeof(req), "KEEP %s", w_template->keep);
        else {
            size_t off = (size_t)snprintf(req, sizeof(req), "BLANK ");
            for (size_t i = 0; i < w_template->blank_count && off + 44 < sizeof(req); ++i)
                off += (size_t)snprintf(req + off, sizeof(req) - off, "%s%s", i ? "\n" : "", w_template->blank_connectors[i]);
        }
        int s_rc = tam_monitor_supervisor_request(vt.number, req, &e);
        if (s_rc >= 0) {
            tam_vt_close(&vt);
            if (json) {
                printf("{\"ok\":%s,\"code\":%d,\"errno\":%d,\"error\":", e.code ? "false" : "true", e.code, e.system_errno);
                quoted_json(e.message);
                puts("}");
            } else if (e.code) {
                fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", e.message, e.code, e.system_errno);
            }
            return e.code ? 1 : 0;
        }
        e.code = TAM_DISPLAY_INVALID;
        strcpy(e.message, "Keep requires --shell for an interactive session or --seconds 1..60 for a bounded trial");
        goto finish;
    }

    struct worker_args w = *w_template;
    const char *first_conn = (w.mode == MODE_KEEP) ? w.keep : w.blank_connectors[0];
    if (resolve_target_card(vt.number, w.card, first_conn, &w.card, &w.verify_cfb, &w.cfb, &e))
        goto finish;
    w.enable_socket = true;

    if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, control) < 0 ||
        sigprocmask(SIG_BLOCK, &mask, &oldmask) < 0) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Cannot prepare recovery channel");
        goto finish;
    }
    child = fork();
    if (!child) {
        sigdelset(&mask, SIGCHLD);
        close(control[0]);
        worker(control[1], vt, &w, &mask);
    }
    if (child < 0) {
        e.code = TAM_DISPLAY_IO; e.system_errno = errno;
        strcpy(e.message, "Cannot start recovery guard");
    }
    close(control[1]); control[1] = -1;
    unsigned vt_num = vt.number;
    tam_vt_close(&vt);
    if (child > 0) {
        int signals = signalfd(-1, &mask, SFD_CLOEXEC | SFD_NONBLOCK);
        struct pollfd fds[] = {{control[0], POLLIN, 0}, {signals, POLLIN, 0}};
        if (signals < 0) shutdown(control[0], SHUT_WR);
        bool ready = false, applied = false, complete = false;
        for (;;) {
            int timeout_ms = (w.seconds > 0) ? (int)(w.seconds + 10) * 1000 : -1;
            int n = poll(fds, 2, timeout_ms);
            if (n < 0 && errno == EINTR) continue;
            if (fds[1].revents & POLLIN) {
                struct signalfd_siginfo si;
                bool quit_signal = false;
                while (read(signals, &si, sizeof(si)) == sizeof(si)) {
                    if (si.ssi_signo == SIGCHLD && shell_pid > 0) {
                        int st = 0;
                        if (waitpid(shell_pid, &st, WNOHANG) == shell_pid) {
                            shell_pid = -1;
                            if (WIFEXITED(st)) shell_exit = WEXITSTATUS(st);
                            else if (WIFSIGNALED(st)) shell_exit = 128 + WTERMSIG(st);
                            quit_signal = true;
                        }
                    } else if (si.ssi_signo != SIGCHLD) {
                        /* If a shell is active in the foreground, ignore Ctrl-C in the parent wrapper;
                         * SIGHUP/SIGTERM terminates the session and restores outputs. */
                        if (shell_pid > 0 && (si.ssi_signo == SIGINT || si.ssi_signo == SIGQUIT || si.ssi_signo == SIGTSTP))
                            continue;
                        quit_signal = true;
                    }
                }
                if (quit_signal) {
                    shutdown(control[0], SHUT_WR);
                    kill(child, SIGCONT);
                }
            } else if (n == 0) {
                shutdown(control[0], SHUT_WR);
                kill(child, SIGCONT);
            }
            if (fds[0].revents & POLLIN) {
                struct report r;
                ssize_t got = recv(control[0], &r, sizeof(r), 0);
                if (got == sizeof(r)) {
                    e.code = r.code; e.system_errno = r.syserr;
                    memcpy(e.message, r.message, sizeof(e.message));
                    e.message[sizeof(e.message) - 1] = 0;
                    if (r.ready == 1 && !ready && !e.code) {
                        ready = true;
                        char go = 'G';
                        if (send(control[0], &go, 1, MSG_NOSIGNAL) != 1)
                            shutdown(control[0], SHUT_WR);
                    } else if (r.ready == 2 && !applied && !e.code) {
                        applied = true;
                        if (spawn_shell) {
                            const char *sh = getenv("TAM_MONITOR_SHELL");
                            if (!sh || !*sh) sh = getenv("SHELL");
                            if (!sh || !*sh) sh = "/bin/sh";
                            shell_pid = fork();
                            if (shell_pid == 0) {
                                close(control[0]);
                                if (signals >= 0) close(signals);
                                sigprocmask(SIG_SETMASK, &oldmask, NULL);
                                char vt_str[32];
                                snprintf(vt_str, sizeof(vt_str), "vt%u", vt_num);
                                setenv("TAM_MONITOR_SESSION", vt_str, 1);
                                if (w.keep) setenv("TAM_MONITOR_KEEP", w.keep, 1);
                                execl(sh, sh, (char *)NULL);
                                _exit(127);
                            } else if (shell_pid < 0) {
                                shutdown(control[0], SHUT_WR);
                            }
                        }
                    } else {
                        complete = true;
                        break;
                    }
                } else break;
            }
            if (!(fds[0].revents & POLLIN) && (fds[0].revents & (POLLHUP | POLLERR | POLLNVAL)))
                break;
        }
        if (shell_pid > 0) {
            kill(shell_pid, SIGHUP);
            int st = 0;
            while (waitpid(shell_pid, &st, 0) < 0 && errno == EINTR) {}
        }
        if (signals >= 0) close(signals);
        while (waitpid(child, &status, 0) < 0 && errno == EINTR) {}
        if (!complete || !WIFEXITED(status) || WEXITSTATUS(status)) {
            if (!e.code) {
                e.code = TAM_DISPLAY_RESTORE_FAILED;
                strcpy(e.message, "Recovery guard failed; kernel fallback is unproven");
            }
        }
    }
    struct timespec zero = {0};
    while (sigtimedwait(&mask, NULL, &zero) >= 0) {}
    sigprocmask(SIG_SETMASK, &oldmask, NULL);
finish:
    tam_vt_close(&vt);
    for (int i = 0; i < 2; ++i) if (control[i] >= 0) close(control[i]);
    if (json) {
        printf("{\"ok\":%s,\"code\":%d,\"errno\":%d,\"error\":", e.code ? "false" : "true", e.code, e.system_errno);
        quoted_json(e.message);
        puts("}");
    } else if (e.code) {
        fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", e.message, e.code, e.system_errno);
    } else if (!spawn_shell) {
        puts("Targeted console monitor selection restored and released.");
    }
    if (e.code) return 1;
    return spawn_shell ? shell_exit : 0;
}

int tam_monitor_keep(unsigned card, const char *keep, bool shell,
    unsigned seconds, int json)
{
    struct worker_args w = {
        .mode = MODE_KEEP,
        .card = card,
        .keep = keep,
        .seconds = seconds
    };
    return run_supervised_session(&w, shell, json);
}

int tam_monitor_blank_monitors(unsigned card, const char *const *connectors,
    size_t count, unsigned seconds, bool seconds_explicit, int json)
{
    struct worker_args w = {
        .mode = MODE_BLANK,
        .card = card,
        .blank_connectors = connectors,
        .blank_count = count,
        .seconds = seconds_explicit ? seconds : 0
    };
    if (!seconds_explicit) {
        struct tam_vt vt = {.fd = -1};
        struct tam_display_error e = {0};
        if (tam_vt_open(&vt, &e) == TAM_DISPLAY_OK) {
            char sock_path[256] = {0};
            bool has_sup = supervisor_socket_path(vt.number, sock_path, sizeof(sock_path), false) &&
                           access(sock_path, F_OK) == 0;
            tam_vt_close(&vt);
            if (has_sup) return run_supervised_session(&w, false, json);
        }
        w.seconds = seconds ? seconds : 15;
    }
    return run_supervised_session(&w, false, json);
}

int tam_monitor_wake(const char *connector, bool all, int json)
{
    struct tam_display_error e = {0};
    struct tam_vt vt = {.fd = -1};
    if (tam_vt_open(&vt, &e)) {
        if (json) {
            printf("{\"ok\":false,\"code\":%d,\"errno\":%d,\"error\":", e.code, e.system_errno);
            quoted_json(e.message);
            puts("}");
        } else {
            fprintf(stderr, "tam-monitor: %s\n", e.message);
        }
        return 1;
    }
    unsigned vt_num = vt.number;
    if (connector && *connector && !all) {
        char req[128];
        snprintf(req, sizeof(req), "WAKE %s", connector);
        int rc = tam_monitor_supervisor_request(vt_num, req, &e);
        if (rc >= 0) {
            tam_vt_close(&vt);
            if (json) {
                printf("{\"ok\":%s,\"code\":%d,\"errno\":%d,\"error\":", e.code ? "false" : "true", e.code, e.system_errno);
                quoted_json(e.message);
                puts("}");
            } else if (e.code) {
                fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", e.message, e.code, e.system_errno);
            }
            return e.code ? 1 : 0;
        }
        /* No active supervisor: verify the connector exists and is connected, then wake VT. */
        struct tam_monitor_info list[TAM_MONITOR_MAX_MONITORS];
        size_t count = 0;
        char hw_err[160] = {0};
        if (tam_monitor_discover(false, list, TAM_MONITOR_MAX_MONITORS, &count, hw_err, sizeof(hw_err)) < 0) {
            tam_vt_close(&vt);
            fprintf(stderr, "tam-monitor: %s\n", hw_err);
            return 1;
        }
        size_t matches = 0, idx = 0;
        for (size_t i = 0; i < count; ++i) {
            if (!strcmp(list[i].id, connector) || !strcmp(list[i].connector, connector)) {
                idx = i;
                ++matches;
            }
        }
        if (matches != 1 || strcmp(list[idx].connection, "connected") != 0) {
            tam_vt_close(&vt);
            e.code = matches > 1 ? TAM_DISPLAY_AMBIGUOUS : matches == 0 ? TAM_DISPLAY_NOT_FOUND : TAM_DISPLAY_UNSUPPORTED;
            snprintf(e.message, sizeof(e.message), "%s",
                matches > 1 ? "Connector name is ambiguous" :
                matches == 0 ? "Selected connector not found" : "Selected connector is not connected");
            if (json) {
                printf("{\"ok\":false,\"code\":%d,\"errno\":0,\"error\":", e.code);
                quoted_json(e.message);
                puts("}");
            } else {
                fprintf(stderr, "tam-monitor: %s\n", e.message);
            }
            return 1;
        }
        tam_vt_wake(&vt, &e);
        tam_vt_close(&vt);
        if (json) {
            printf("{\"ok\":%s,\"code\":%d,\"errno\":%d}\n", e.code ? "false" : "true", e.code, e.system_errno);
        } else if (e.code) {
            fprintf(stderr, "tam-monitor: %s\n", e.message);
        }
        return e.code ? 1 : 0;
    }

    /* wake or wake --all */
    struct tam_display_error sup_err = {0};
    int sup_rc = tam_monitor_supervisor_request(vt_num, "RESTORE", &sup_err);
    tam_vt_wake(&vt, &e);
    tam_vt_close(&vt);
    if (sup_rc > 0 && sup_err.code) e = sup_err;
    if (json) {
        printf("{\"ok\":%s,\"code\":%d,\"errno\":%d}\n", e.code ? "false" : "true", e.code, e.system_errno);
    } else if (e.code) {
        fprintf(stderr, "tam-monitor: %s\n", e.message);
    }
    return e.code ? 1 : 0;
}

static long long mono_ms(void)
{
    struct timespec ts = {0};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000LL + ts.tv_nsec / 1000000LL;
}

static int run_blank_guard_loop(int vt_fd, int control_fd, unsigned seconds,
    pid_t pgrp, const struct termios *restore)
{
    struct tam_vt vt = {
        .fd = vt_fd,
        .number = 0,
        .uid = getuid(),
        .foreground_group = pgrp
    };
    struct stat st;
    if (fstat(vt_fd, &st) == 0) vt.number = (unsigned)(st.st_rdev & 0xff);
    struct tam_display_error e = {0};
    bool blanked = false, disconnected = false;
    int status = 0;

    if (tam_vt_check(&vt, &e) != TAM_DISPLAY_OK ||
        flock(vt.fd, LOCK_EX | LOCK_NB) < 0 ||
        tam_vt_check(&vt, &e) != TAM_DISPLAY_OK) {
        if (!e.code) snprintf(e.message, sizeof(e.message), "Cannot lock controlling console: %s", strerror(errno));
        char pkt[180];
        int len = snprintf(pkt, sizeof(pkt), "E%s", e.message);
        (void)send(control_fd, pkt, (size_t)len, MSG_NOSIGNAL);
        return 1;
    }
    blanked = true;
    if (tam_vt_blank(&vt, &e) != TAM_DISPLAY_OK) {
        status = 1;
        char pkt[180];
        int len = snprintf(pkt, sizeof(pkt), "E%s", e.message);
        (void)send(control_fd, pkt, (size_t)len, MSG_NOSIGNAL);
        goto cleanup;
    }
    (void)send(control_fd, "B", 1, MSG_NOSIGNAL);
    long long deadline = mono_ms() + (long long)seconds * 1000LL;
    while (mono_ms() < deadline && tam_vt_check_restore(&vt, &e) == TAM_DISPLAY_OK) {
        long long rem = deadline - mono_ms();
        int wait_ms = rem > 100 ? 100 : (int)(rem > 0 ? rem : 0);
        struct pollfd pfd = {.fd = control_fd, .events = POLLIN};
        int n = poll(&pfd, 1, wait_ms);
        if (n > 0 && (pfd.revents & (POLLIN | POLLHUP | POLLERR))) {
            char buf[16];
            ssize_t got = recv(control_fd, buf, sizeof(buf), 0);
            disconnected = (got <= 0);
            break;
        }
    }
cleanup:
    if (blanked) {
        if (tam_vt_check_restore(&vt, &e) == TAM_DISPLAY_OK) {
            if (tam_vt_wake(&vt, &e) != TAM_DISPLAY_OK) {
                status = 1;
                char pkt[180];
                int len = snprintf(pkt, sizeof(pkt), "E%s", e.message);
                (void)send(control_fd, pkt, (size_t)len, MSG_NOSIGNAL);
            }
        }
        if (disconnected && tcgetpgrp(vt.fd) == pgrp && restore) {
            (void)tcsetattr(vt.fd, TCSANOW, restore);
        }
        if (status == 0) (void)send(control_fd, "W", 1, MSG_NOSIGNAL);
    }
    (void)flock(vt.fd, LOCK_UN);
    return status;
}

int tam_monitor_guard_entry(int argc, char **argv)
{
    if (argc != 4) return 2;
    int fd = atoi(argv[0]);
    int control_fd = atoi(argv[1]);
    int seconds = atoi(argv[2]);
    pid_t pgrp = (pid_t)atol(argv[3]);
    if (fd < 0 || control_fd < 0 || seconds < 1 || seconds > 60 || pgrp <= 0)
        return 2;
    const int ign[] = {SIGHUP, SIGINT, SIGTSTP, SIGTTIN, SIGTTOU};
    for (size_t i = 0; i < sizeof(ign)/sizeof(*ign); ++i) signal(ign[i], SIG_IGN);
    struct timeval tv = {.tv_sec = 3, .tv_usec = 0};
    setsockopt(control_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    struct termios restore = {0};
    ssize_t got = recv(control_fd, &restore, sizeof(restore), 0);
    if (got != sizeof(restore)) {
        close(control_fd);
        return 1;
    }
    struct timeval zero_tv = {0};
    setsockopt(control_fd, SOL_SOCKET, SO_RCVTIMEO, &zero_tv, sizeof(zero_tv));
    int rc = run_blank_guard_loop(fd, control_fd, (unsigned)seconds, pgrp, &restore);
    close(control_fd);
    return rc;
}

int tam_monitor_blank_console(unsigned seconds,
    const struct termios *restore_termios, char *err, size_t err_cap)
{
    if (err && err_cap) err[0] = 0;
    if (seconds < 1 || seconds > 60) {
        if (err && err_cap) snprintf(err, err_cap, "Blank duration must be 1-60 seconds");
        return 1;
    }
    struct tam_vt vt = {.fd = -1};
    struct tam_display_error e = {0};
    if (tam_vt_open(&vt, &e) != TAM_DISPLAY_OK) {
        if (err && err_cap) snprintf(err, err_cap, "%s", e.message);
        return 1;
    }
    struct termios saved = {0};
    if (tcgetattr(vt.fd, &saved) < 0) {
        if (err && err_cap) snprintf(err, err_cap, "Cannot read terminal settings: %s", strerror(errno));
        tam_vt_close(&vt);
        return 1;
    }
    struct termios target_restore = restore_termios ? *restore_termios : saved;
    int sp[2] = {-1, -1};
    if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sp) < 0) {
        if (err && err_cap) snprintf(err, err_cap, "Cannot create wake guard channel");
        tam_vt_close(&vt);
        return 1;
    }
    struct termios cbreak = saved;
    cbreak.c_lflag &= ~(tcflag_t)(ICANON | ECHO);
    cbreak.c_cc[VMIN] = 1;
    cbreak.c_cc[VTIME] = 0;
    (void)tcsetattr(vt.fd, TCSANOW, &cbreak);

    sigset_t mask, oldmask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGINT);
    sigaddset(&mask, SIGTERM);
    sigaddset(&mask, SIGHUP);
    sigprocmask(SIG_BLOCK, &mask, &oldmask);
    int sigfd = signalfd(-1, &mask, SFD_CLOEXEC | SFD_NONBLOCK);

    pid_t pid = fork();
    if (pid == 0) {
        setpgid(0, 0);
        close(sp[0]);
        if (sigfd >= 0) close(sigfd);
        sigprocmask(SIG_SETMASK, &oldmask, NULL);
        const int ign[] = {SIGHUP, SIGINT, SIGTSTP, SIGTTIN, SIGTTOU};
        for (size_t i = 0; i < sizeof(ign)/sizeof(*ign); ++i) signal(ign[i], SIG_IGN);
        struct timeval tv = {.tv_sec = 3, .tv_usec = 0};
        setsockopt(sp[1], SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        struct termios r_term = {0};
        if (recv(sp[1], &r_term, sizeof(r_term), 0) != sizeof(r_term)) {
            close(sp[1]);
            _exit(1);
        }
        struct timeval zero_tv = {0};
        setsockopt(sp[1], SOL_SOCKET, SO_RCVTIMEO, &zero_tv, sizeof(zero_tv));
        int rc = run_blank_guard_loop(vt.fd, sp[1], seconds, vt.foreground_group, &r_term);
        close(sp[1]);
        tam_vt_close(&vt);
        _exit(rc);
    }
    close(sp[1]);
    int exit_code = 0;
    if (pid < 0) {
        if (err && err_cap) snprintf(err, err_cap, "Cannot start wake guard");
        exit_code = 1;
        goto cleanup;
    }
    struct timeval tv = {.tv_sec = 3, .tv_usec = 0};
    setsockopt(sp[0], SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sp[0], SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
    if (send(sp[0], &target_restore, sizeof(target_restore), MSG_NOSIGNAL) != sizeof(target_restore)) {
        if (err && err_cap) snprintf(err, err_cap, "Wake guard did not arm; console not blanked");
        exit_code = 1;
        goto cleanup;
    }
    char pkt[256] = {0};
    ssize_t got = recv(sp[0], pkt, sizeof(pkt) - 1, 0);
    if (got != 1 || pkt[0] != 'B') {
        if (err && err_cap) {
            if (got > 1 && pkt[0] == 'E') snprintf(err, err_cap, "%s", pkt + 1);
            else snprintf(err, err_cap, "Wake guard did not arm; console not blanked");
        }
        exit_code = 1;
        goto cleanup;
    }
    struct timeval zero_tv = {0};
    setsockopt(sp[0], SOL_SOCKET, SO_RCVTIMEO, &zero_tv, sizeof(zero_tv));

    for (;;) {
        struct pollfd fds[3] = {
            {.fd = vt.fd, .events = POLLIN},
            {.fd = sp[0], .events = POLLIN},
            {.fd = sigfd, .events = POLLIN}
        };
        int n = poll(fds, 3, 100);
        if (n < 0 && errno == EINTR) continue;
        if (sigfd >= 0 && (fds[2].revents & POLLIN)) {
            struct signalfd_siginfo si;
            if (read(sigfd, &si, sizeof(si)) == sizeof(si) && si.ssi_signo == SIGINT)
                exit_code = 130;
            else
                exit_code = 1;
            (void)send(sp[0], "Q", 1, MSG_NOSIGNAL);
            break;
        }
        if (fds[1].revents & (POLLIN | POLLHUP | POLLERR)) {
            ssize_t r = recv(sp[0], pkt, sizeof(pkt) - 1, 0);
            if (r > 1 && pkt[0] == 'E') {
                pkt[r] = 0;
                if (err && err_cap) snprintf(err, err_cap, "%s", pkt + 1);
                exit_code = 1;
            }
            break;
        }
        if (fds[0].revents & POLLIN) {
            char ch = 0;
            if (read(vt.fd, &ch, 1) == 1 && ch == 3) exit_code = 130;
            (void)send(sp[0], "K", 1, MSG_NOSIGNAL);
            break;
        }
    }
cleanup:
    if (sp[0] >= 0) { close(sp[0]); sp[0] = -1; }
    if (pid > 0) {
        int st = 0;
        long long wait_deadline = mono_ms() + 3000;
        bool reaped = false;
        while (mono_ms() < wait_deadline) {
            pid_t w = waitpid(pid, &st, WNOHANG);
            if (w == pid) { reaped = true; break; }
            struct timespec sl = {.tv_sec = 0, .tv_nsec = 20000000};
            nanosleep(&sl, NULL);
        }
        if (!reaped) {
            if (err && err_cap && !err[0]) snprintf(err, err_cap, "Wake guard is still recovering the console");
            if (!exit_code) exit_code = 1;
        } else if ((!WIFEXITED(st) || WEXITSTATUS(st) != 0) && !exit_code) {
            if (err && err_cap && !err[0]) snprintf(err, err_cap, "Wake guard reported a console or recovery failure");
            exit_code = 1;
        }
    }
    if (sigfd >= 0) close(sigfd);
    struct timespec zero = {0};
    while (sigtimedwait(&mask, NULL, &zero) >= 0) {}
    sigprocmask(SIG_SETMASK, &oldmask, NULL);
    if (tcgetpgrp(vt.fd) == getpgrp())
        (void)tcsetattr(vt.fd, TCSANOW, &saved);
    tam_vt_close(&vt);
    return exit_code;
}
