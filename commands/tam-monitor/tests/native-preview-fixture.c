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
static int event = -1, applied, hotplug, recovery_required;
static char detached_name[64];
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
    const char *log = getenv("TAM_MONITOR_FIXTURE_LOG");
    if (!log || !*log) return;
    int fd = open(log, O_WRONLY | O_APPEND | O_CLOEXEC);
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
enum tam_display_result __wrap_tam_vt_check_restore(const struct tam_vt *v, struct tam_display_error *e)
{ (void)v; (void)e; return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_vt_claim(struct tam_vt *v, struct tam_display_error *e)
{ (void)e; v->claimed = true; return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_vt_release(struct tam_vt *v, bool handoff, struct tam_display_error *e)
{ (void)e; (void)handoff; v->claimed = false; return TAM_DISPLAY_OK; }
void __wrap_tam_vt_close(struct tam_vt *v) { if (v->fd >= 0) { close(v->fd); v->fd = -1; } }
enum tam_display_result __wrap_tam_vt_blank(const struct tam_vt *v, struct tam_display_error *e)
{ (void)v; (void)e; record("vt_blank"); return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_vt_wake(const struct tam_vt *v, struct tam_display_error *e)
{ (void)v; (void)e; record("vt_wake"); return TAM_DISPLAY_OK; }
enum tam_display_result __wrap_tam_display_map_console_fb(unsigned vt_number,
    struct tam_console_fb *out, struct tam_display_error *e)
{
    if (flag("TAM_MONITOR_FIXTURE_MAP_FAIL")) return fail(e, TAM_DISPLAY_UNSUPPORTED);
    memset(out, 0, sizeof(*out));
    out->vt_number = vt_number;
    out->fb_index = 0;
    out->card = 1;
    strcpy(out->fb_name, "amdgpudrmfb");
    out->width = 1920;
    out->height = 1080;
    out->stride = 7680;
    out->bits_per_pixel = 32;
    out->con2fb_verified = true;
    return TAM_DISPLAY_OK;
}
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
enum tam_display_result __wrap_tam_display_state_verify_console_fb(
    struct tam_display_state *s, struct tam_console_fb *fb, struct tam_display_error *e)
{
    (void)s;
    if (flag("TAM_MONITOR_FIXTURE_CFB_FAIL")) return fail(e, TAM_DISPLAY_UNSUPPORTED);
    if (flag("TAM_MONITOR_FIXTURE_VERBOSE")) record("verify_cfb");
    if (fb) fb->drm_fb_id = 77;
    return TAM_DISPLAY_OK;
}
void __wrap_tam_display_state_set_access_check(struct tam_display_state *s, tam_display_access_check check, void *context)
{ (void)s; access_check = check; access_context = context; }
enum tam_display_result __wrap_tam_display_state_keep(struct tam_display_state *s, const char *name, struct tam_display_error *e)
{
    (void)s;
    if (flag("TAM_MONITOR_FIXTURE_SLOW_TEST")) usleep(1500000);
    if (access_check(access_context, false, e)) return e->code;
    record("apply");
    if (flag("TAM_MONITOR_FIXTURE_VERBOSE") && name) {
        char buf[96];
        snprintf(buf, sizeof(buf), "keep:%s", name);
        record(buf);
    }
    applied = 1;
    snprintf(detached_name, sizeof(detached_name), "%s", (name && !strcmp(name, "HDMI-A-1")) ? "DP-1" : "HDMI-A-1");
    if (flag("TAM_MONITOR_FIXTURE_PAUSE")) kill(getpid(), SIGUSR1);
    if (flag("TAM_MONITOR_FIXTURE_HOTPLUG")) { uint64_t one = 1; if (write(hotplug, &one, sizeof(one)) < 0) abort(); }
    if (flag("TAM_MONITOR_FIXTURE_COMMIT_FAIL")) return fail(e, TAM_DISPLAY_IO);
    return TAM_DISPLAY_OK;
}
enum tam_display_result __wrap_tam_display_state_blank(struct tam_display_state *s,
    const char *const *connectors, size_t count, struct tam_display_error *e)
{
    (void)s;
    if (access_check(access_context, false, e)) return e->code;
    if (!connectors || !count) return fail(e, TAM_DISPLAY_INVALID);
    record("apply");
    if (flag("TAM_MONITOR_FIXTURE_VERBOSE") && connectors[0]) {
        char buf[96];
        snprintf(buf, sizeof(buf), "blank:%s", connectors[0]);
        record(buf);
    }
    applied = 1;
    snprintf(detached_name, sizeof(detached_name), "%s", connectors[0]);
    if (flag("TAM_MONITOR_FIXTURE_INTERACTIVE_UNCERTAIN")) {
        recovery_required = 1;
        return fail(e, TAM_DISPLAY_IO);
    }
    if (flag("TAM_MONITOR_FIXTURE_COMMIT_FAIL")) return fail(e, TAM_DISPLAY_IO);
    return TAM_DISPLAY_OK;
}
enum tam_display_result __wrap_tam_display_state_wake(struct tam_display_state *s,
    const char *connector, struct tam_display_error *e)
{
    (void)s;
    if (access_check(access_context, false, e)) return e->code;
    if (!connector || !*connector) return fail(e, TAM_DISPLAY_INVALID);
    if (!strcmp(connector, "missing")) return fail(e, TAM_DISPLAY_NOT_FOUND);
    if (flag("TAM_MONITOR_FIXTURE_VERBOSE")) {
        char buf[96];
        snprintf(buf, sizeof(buf), "wake:%s", connector);
        record(buf);
    } else {
        record("wake");
    }
    const char *bare = connector;
    if (!strncmp(bare, "card", 4)) {
        const char *dash = strchr(bare, '-');
        if (dash) bare = dash + 1;
    }
    if (!strcmp(detached_name, bare)) detached_name[0] = 0;
    return TAM_DISPLAY_OK;
}
bool __wrap_tam_display_state_is_detached(const struct tam_display_state *s, const char *connector)
{
    (void)s;
    if (connector && !strncmp(connector, "card", 4)) {
        const char *dash = strchr(connector, '-');
        if (dash) connector = dash + 1;
    }
    return connector && detached_name[0] && !strcmp(detached_name, connector);
}
bool __wrap_tam_display_state_recovery_required(const struct tam_display_state *s)
{
    (void)s;
    return recovery_required;
}
enum tam_display_result __wrap_tam_display_state_restore(struct tam_display_state *s, struct tam_display_error *e)
{
    (void)s;
    if (access_check(access_context, true, e)) return e->code;
    record("restore");
    detached_name[0] = 0;
    if (flag("TAM_MONITOR_FIXTURE_NO_OUTPUT")) {
        fail(e, TAM_DISPLAY_RESTORE_FAILED);
        strcpy(e->message, "No captured connected console output remains; releasing display control");
        return e->code;
    }
    if (flag("TAM_MONITOR_FIXTURE_RESTORE_FAIL")) return fail(e, TAM_DISPLAY_RESTORE_FAILED);
    return TAM_DISPLAY_OK;
}
void __wrap_tam_display_state_free(struct tam_display_state *s) { if (s) { record("free"); free(s); } }
