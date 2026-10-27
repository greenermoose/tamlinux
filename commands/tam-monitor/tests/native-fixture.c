#define _GNU_SOURCE
#include <tam_display.h>
#include <tam_vt.h>
#include "../native-hw.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

/* Linked only into the test executable; never an environment hook in product. */
extern const char *__real_tam_monitor_sysfs_drm_path(void);
extern const char *__real_tam_monitor_sysfs_backlight_path(void);
extern const char *__real_tam_monitor_consoleblank_path(void);
extern int __real_tam_monitor_run_tool(const char *const *argv,
    char *out, size_t out_cap, char *err, size_t err_cap);
extern enum tam_display_result __real_tam_vt_open(struct tam_vt *v, struct tam_display_error *e);
extern enum tam_display_result __real_tam_vt_check(const struct tam_vt *v, struct tam_display_error *e);
extern enum tam_display_result __real_tam_vt_check_restore(const struct tam_vt *v, struct tam_display_error *e);
extern enum tam_display_result __real_tam_vt_blank(const struct tam_vt *v, struct tam_display_error *e);
extern enum tam_display_result __real_tam_vt_wake(const struct tam_vt *v, struct tam_display_error *e);
extern enum tam_display_result __real_tam_vt_idle_path(const struct tam_vt *v, unsigned minutes,
    const char *param_path, bool *verified, struct tam_display_error *e);
extern void __real_tam_vt_close(struct tam_vt *v);

const char *__wrap_tam_monitor_sysfs_drm_path(void)
{
    const char *p = getenv("TAM_MONITOR_FIXTURE_DRM");
    return (p && *p) ? p : __real_tam_monitor_sysfs_drm_path();
}

const char *__wrap_tam_monitor_sysfs_backlight_path(void)
{
    const char *p = getenv("TAM_MONITOR_FIXTURE_BACKLIGHT");
    return (p && *p) ? p : __real_tam_monitor_sysfs_backlight_path();
}

const char *__wrap_tam_monitor_consoleblank_path(void)
{
    const char *p = getenv("TAM_MONITOR_FIXTURE_CONSOLEBLANK");
    return (p && *p) ? p : __real_tam_monitor_consoleblank_path();
}

int __wrap_tam_monitor_run_tool(const char *const *argv,
    char *out, size_t out_cap, char *err, size_t err_cap)
{
    const char *log_path = getenv("TAM_MONITOR_FIXTURE_TOOL_LOG");
    if (log_path && *log_path && argv && argv[0]) {
        int fd = open(log_path, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
        if (fd >= 0) {
            for (size_t i = 0; argv[i]; ++i)
                dprintf(fd, "%s%s", i ? "\t" : "", argv[i]);
            dprintf(fd, "\n");
            close(fd);
        }
    }
    const char *t_env = getenv("TAM_MONITOR_FIXTURE_TOOL_TIMEOUT_MS");
    if (t_env && *t_env) {
        return tam_monitor_run_tool_timeout(argv, atoi(t_env), out, out_cap, err, err_cap);
    }
    return __real_tam_monitor_run_tool(argv, out, out_cap, err, err_cap);
}

static bool vt_fixture_active(bool require_foreground, struct tam_display_error *e)
{
    const char *foreign = getenv("TAM_MONITOR_FIXTURE_VT_FOREIGN");
    if (foreign && *foreign) {
        if (e) {
            e->code = TAM_DISPLAY_PERMISSION;
            e->system_errno = 0;
            strcpy(e->message, "Text VT must belong to the calling user");
        }
        return false;
    }
    const char *state_path = getenv("TAM_MONITOR_FIXTURE_VT_STATE");
    if (state_path && *state_path) {
        int fd = open(state_path, O_RDONLY | O_CLOEXEC);
        char buf[32] = {0};
        if (fd >= 0) {
            ssize_t n = read(fd, buf, sizeof(buf) - 1);
            if (n > 0) buf[n] = 0;
            close(fd);
        }
        if (strncmp(buf, "yes", 3) != 0) {
            if (e) {
                e->code = TAM_DISPLAY_INACTIVE;
                e->system_errno = 0;
                strcpy(e->message, "Owned text VT and command must be in the foreground");
            }
            return false;
        }
    }
    const char *bg = getenv("TAM_MONITOR_FIXTURE_VT_BG");
    if (require_foreground && bg && *bg) {
        if (e) {
            e->code = TAM_DISPLAY_INACTIVE;
            e->system_errno = 0;
            strcpy(e->message, "Owned text VT and command must be in the foreground");
        }
        return false;
    }
    return true;
}

static void record_vt_event(const char *ev)
{
    const char *p = getenv("TAM_MONITOR_FIXTURE_VT_EVENTS");
    if (!p || !*p) return;
    int fd = open(p, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
    if (fd >= 0) {
        dprintf(fd, "%s\n", ev);
        close(fd);
    }
}

enum tam_display_result __wrap_tam_vt_open(struct tam_vt *v, struct tam_display_error *e)
{
    const char *mode = getenv("TAM_MONITOR_FIXTURE_VT");
    if (!mode || !*mode) return __real_tam_vt_open(v, e);
    if (!strcmp(mode, "deny")) {
        if (e) {
            e->code = TAM_DISPLAY_INACTIVE;
            e->system_errno = 0;
            strcpy(e->message, "fixture PTY");
        }
        return TAM_DISPLAY_INACTIVE;
    }
    if (!vt_fixture_active(true, e)) return e->code;
    int fd = open("/dev/tty", O_RDWR | O_NOCTTY | O_CLOEXEC);
    if (fd < 0) fd = dup(STDIN_FILENO);
    if (fd < 0) {
        if (e) {
            e->code = TAM_DISPLAY_INACTIVE;
            e->system_errno = errno;
            strcpy(e->message, "No controlling terminal in fixture");
        }
        return TAM_DISPLAY_INACTIVE;
    }
    v->fd = fd;
    v->number = 2;
    v->uid = getuid();
    v->foreground_group = getpgrp();
    v->claimed = false;
    return TAM_DISPLAY_OK;
}

enum tam_display_result __wrap_tam_vt_check(const struct tam_vt *v, struct tam_display_error *e)
{
    const char *mode = getenv("TAM_MONITOR_FIXTURE_VT");
    if (!mode || !*mode) return __real_tam_vt_check(v, e);
    if (!vt_fixture_active(true, e)) return e->code;
    if (v && v->fd >= 0 && v->foreground_group > 0) {
        pid_t fg = tcgetpgrp(v->fd);
        if (fg > 0 && fg != v->foreground_group) {
            if (e) {
                e->code = TAM_DISPLAY_INACTIVE;
                e->system_errno = 0;
                strcpy(e->message, "Owned text VT and command must be in the foreground");
            }
            return TAM_DISPLAY_INACTIVE;
        }
    }
    return TAM_DISPLAY_OK;
}

enum tam_display_result __wrap_tam_vt_check_restore(const struct tam_vt *v, struct tam_display_error *e)
{
    const char *mode = getenv("TAM_MONITOR_FIXTURE_VT");
    if (!mode || !*mode) return __real_tam_vt_check_restore(v, e);
    if (!vt_fixture_active(false, e)) return e->code;
    return TAM_DISPLAY_OK;
}

enum tam_display_result __wrap_tam_vt_blank(const struct tam_vt *v, struct tam_display_error *e)
{
    const char *mode = getenv("TAM_MONITOR_FIXTURE_VT");
    if (!mode || !*mode) return __real_tam_vt_blank(v, e);
    if (!vt_fixture_active(true, e)) return e->code;
    record_vt_event("blank");
    return TAM_DISPLAY_OK;
}

enum tam_display_result __wrap_tam_vt_wake(const struct tam_vt *v, struct tam_display_error *e)
{
    const char *mode = getenv("TAM_MONITOR_FIXTURE_VT");
    if (!mode || !*mode) return __real_tam_vt_wake(v, e);
    if (!vt_fixture_active(false, e)) return e->code;
    record_vt_event("wake");
    return TAM_DISPLAY_OK;
}

enum tam_display_result __wrap_tam_vt_idle_path(const struct tam_vt *v, unsigned minutes,
    const char *param_path, bool *verified, struct tam_display_error *e)
{
    const char *mode = getenv("TAM_MONITOR_FIXTURE_VT");
    if (!mode || !*mode) return __real_tam_vt_idle_path(v, minutes, param_path, verified, e);
    if (verified) *verified = false;
    if (minutes > 60) {
        if (e) { e->code = TAM_DISPLAY_INVALID; e->system_errno = 0; strcpy(e->message, "Idle interval must be 0-60 minutes"); }
        return TAM_DISPLAY_INVALID;
    }
    if (__wrap_tam_vt_check(v, e) != TAM_DISPLAY_OK) return e->code;
    char seq[32];
    int len = snprintf(seq, sizeof(seq), "\x1b[9;%u]", minutes);
    if (len <= 0 || write(v->fd, seq, (size_t)len) != len) {
        if (e) { e->code = TAM_DISPLAY_IO; e->system_errno = errno; strcpy(e->message, "Cannot write console idle sequence"); }
        return TAM_DISPLAY_IO;
    }
    (void)tcdrain(v->fd);
    const char *check_path = getenv("TAM_MONITOR_FIXTURE_CONSOLEBLANK");
    if (!check_path || !*check_path) check_path = param_path;
    int actual = -1;
    if (tam_vt_idle_seconds_path(check_path, &actual) == TAM_DISPLAY_OK) {
        if (actual != (int)(minutes * 60)) {
            if (e) { e->code = TAM_DISPLAY_IO; e->system_errno = 0; strcpy(e->message, "Console idle interval verification failed"); }
            return TAM_DISPLAY_IO;
        }
        if (verified) *verified = true;
    }
    return TAM_DISPLAY_OK;
}

void __wrap_tam_vt_close(struct tam_vt *v)
{
    __real_tam_vt_close(v);
}

enum tam_display_result __wrap_tam_display_inspect_fd(int fd,
    struct tam_display_topology **out, struct tam_display_error *error)
{
    (void)fd;
    *out = calloc(1, sizeof(**out));
    if (!*out) { error->system_errno = ENOMEM; return TAM_DISPLAY_IO; }
    struct tam_display_topology *t = *out;
    strcpy(t->driver, "fixture\"driver\\");
    t->connector_count = 3; t->crtc_count = 2; t->plane_count = 2;
    for (int i = 0; i < 3; ++i) {
        struct tam_display_connector *c = &t->connectors[i];
        c->object.id = 100 + i; c->connection = 1; c->crtc_id = i < 2 ? 10 : 11;
        strcpy(c->name, i == 0 ? "DP-1" : i == 1 ? "DP-2" : "HDMI-A-1");
        c->object.property_count = 1;
        strcpy(c->object.properties[0].name, "CRTC_ID");
        c->object.properties[0].value = c->crtc_id;
    }
    for (int i = 0; i < 2; ++i) {
        t->crtcs[i].object.id = 10 + i;
        t->crtcs[i].mode_valid = true; t->crtcs[i].framebuffer_id = 77;
        t->planes[i].object.id = 200 + i; t->planes[i].crtc_id = 10 + i;
        t->planes[i].framebuffer_id = 77;
    }
    return TAM_DISPLAY_OK;
}
