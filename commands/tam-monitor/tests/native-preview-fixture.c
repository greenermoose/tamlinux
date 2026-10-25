#define _GNU_SOURCE
#include <tam_display_session.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/eventfd.h>
#include <unistd.h>

/* Link-time fixture only; product has no environment substitution hooks. */
static int event = -1, applied, hotplug;
int __wrap_tam_monitor_hotplug_open(void) { hotplug = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK); return hotplug; }
bool __wrap_tam_monitor_hotplug_event(int fd)
{
    (void)fd;
    return applied && getenv("TAM_MONITOR_FIXTURE_HOTPLUG");
}
static tam_display_access_check access_check;
static void *access_context;
static void record(const char *action)
{
    int fd = open(getenv("TAM_MONITOR_FIXTURE_LOG"), O_WRONLY | O_APPEND | O_CLOEXEC);
    if (fd >= 0) { dprintf(fd, "%s %ld\n", action, (long)getpid()); close(fd); }
}
static int flag(const char *name) { const char *v = getenv(name); return v && *v; }
static enum tam_display_result fail(struct tam_display_error *e, enum tam_display_result code)
{ e->code = code; e->system_errno = EIO; strcpy(e->message, "Injected fixture failure"); return code; }
enum tam_display_result __wrap_tam_vt_open(struct tam_vt *v, struct tam_display_error *e)
{
    (void)e; v->fd = open("/dev/null", O_RDWR | O_CLOEXEC); v->number = 2;
    v->uid = getuid(); v->foreground_group = getpgrp(); return TAM_DISPLAY_OK;
}
enum tam_display_result __wrap_tam_vt_check(const struct tam_vt *v, struct tam_display_error *e)
{ (void)v; (void)e; return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_vt_claim(struct tam_vt *v, struct tam_display_error *e)
{ (void)e; v->claimed = true; return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_vt_release(struct tam_vt *v, bool handoff, struct tam_display_error *e)
{ (void)e; (void)handoff; v->claimed = false; return TAM_DISPLAY_OK; }
void __wrap_tam_vt_close(struct tam_vt *v) { if (v->fd >= 0) { close(v->fd); v->fd = -1; } }
enum tam_display_result __wrap_tam_display_session_open(const struct tam_vt *v, unsigned card,
    struct tam_display_session **out, struct tam_display_error *e)
{
    (void)v; (void)card; record("acquire");
    if (flag("TAM_MONITOR_FIXTURE_DENIED")) { *out = NULL; return fail(e, TAM_DISPLAY_PERMISSION); }
    event = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK); *out = malloc(1); return TAM_DISPLAY_OK;
}
int __wrap_tam_display_session_device(const struct tam_display_session *s) { (void)s; return 42; }
int __wrap_tam_display_session_bus_fd(struct tam_display_session *s) { (void)s; return event; }
int __wrap_tam_display_session_bus_events(struct tam_display_session *s) { (void)s; return POLLIN; }
enum tam_display_session_event __wrap_tam_display_session_dispatch(struct tam_display_session *s)
{
    (void)s;
    if (applied && flag("TAM_MONITOR_FIXTURE_REVOKE")) return TAM_DISPLAY_SESSION_LOST;

    return TAM_DISPLAY_SESSION_RUNNING;
}
enum tam_display_result __wrap_tam_display_session_check(struct tam_display_session *s, struct tam_display_error *e)
{ (void)s; (void)e; return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_display_session_check_restore(struct tam_display_session *s, struct tam_display_error *e)
{
    (void)s;
    if (applied && flag("TAM_MONITOR_FIXTURE_REVOKE")) return fail(e, TAM_DISPLAY_RESTORE_FAILED);
    return TAM_DISPLAY_OK;
}
void __wrap_tam_display_session_close(struct tam_display_session *s)
{ if (s) { record("release"); free(s); close(event); } }
enum tam_display_result __wrap_tam_display_capture_fd(int fd, struct tam_display_state **out, struct tam_display_error *e)
{
    (void)fd; record("capture");
    if (flag("TAM_MONITOR_FIXTURE_CAPTURE_FAIL")) { *out = NULL; return fail(e, TAM_DISPLAY_UNSUPPORTED); }
    if (flag("TAM_MONITOR_FIXTURE_SLOW_CAPTURE")) usleep(1500000);
    *out = malloc(1); return TAM_DISPLAY_OK;
}
void __wrap_tam_display_state_set_access_check(struct tam_display_state *s, tam_display_access_check check, void *context)
{ (void)s; access_check = check; access_context = context; }
enum tam_display_result __wrap_tam_display_state_keep(struct tam_display_state *s, const char *name, struct tam_display_error *e)
{
    (void)s; (void)name;
    if (flag("TAM_MONITOR_FIXTURE_SLOW_TEST")) usleep(1500000);
    if (access_check(access_context, false, e)) return e->code;
    record("apply"); applied = 1;
    if (flag("TAM_MONITOR_FIXTURE_PAUSE")) kill(getpid(), SIGUSR1);
    if (flag("TAM_MONITOR_FIXTURE_HOTPLUG")) { uint64_t one = 1; if (write(hotplug, &one, sizeof(one)) < 0) abort(); }
    if (flag("TAM_MONITOR_FIXTURE_COMMIT_FAIL")) return fail(e, TAM_DISPLAY_IO);
    return TAM_DISPLAY_OK;
}
enum tam_display_result __wrap_tam_display_state_restore(struct tam_display_state *s, struct tam_display_error *e)
{
    (void)s;
    if (access_check(access_context, true, e)) return e->code;
    record("restore");
    if (flag("TAM_MONITOR_FIXTURE_RESTORE_FAIL")) return fail(e, TAM_DISPLAY_RESTORE_FAILED);
    return TAM_DISPLAY_OK;
}
void __wrap_tam_display_state_free(struct tam_display_state *s) { if (s) { record("free"); free(s); } }
