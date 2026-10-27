#define _GNU_SOURCE
#include "native-hw.h"
#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

void tam_monitor_clean(const char *src, char *dst, size_t cap)
{
    if (!dst || !cap) return;
    if (!src) { dst[0] = 0; return; }
    size_t limit = cap - 1;
    if (limit > 160) limit = 160;
    size_t i = 0;
    for (; src[i] && i < limit; ++i) {
        unsigned char c = (unsigned char)src[i];
        dst[i] = (c >= 32 && c <= 126) ? (char)c : '?';
    }
    dst[i] = 0;
}

static void trim_inplace(char *s)
{
    size_t len = strlen(s);
    while (len > 0 && (s[len - 1] == ' ' || s[len - 1] == '\t' || s[len - 1] == '\n' || s[len - 1] == '\r'))
        s[--len] = 0;
    size_t start = 0;
    while (s[start] == ' ' || s[start] == '\t' || s[start] == '\n' || s[start] == '\r')
        ++start;
    if (start > 0) memmove(s, s + start, len - start + 1);
}

static void read_text_file(const char *path, char *out, size_t cap)
{
    if (!out || !cap) return;
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        snprintf(out, cap, "unknown");
        return;
    }
    char buf[4096];
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n < 0) {
        snprintf(out, cap, "unknown");
        return;
    }
    buf[n] = 0;
    trim_inplace(buf);
    size_t len = strlen(buf);
    if (len >= cap) len = cap - 1;
    memcpy(out, buf, len);
    out[len] = 0;
}

void tam_monitor_edid_identity(const char *path, char *out, size_t cap)
{
    if (!out || !cap) return;
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) {
        snprintf(out, cap, "EDID unavailable");
        return;
    }
    unsigned char data[128];
    ssize_t n = read(fd, data, sizeof(data));
    close(fd);
    static const unsigned char header[8] = {0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00};
    unsigned sum = 0;
    if (n != 128 || memcmp(data, header, 8) != 0) {
        snprintf(out, cap, "EDID unavailable");
        return;
    }
    for (int i = 0; i < 128; ++i) sum += data[i];
    if ((sum & 0xff) != 0) {
        snprintf(out, cap, "EDID unavailable");
        return;
    }
    unsigned code = ((unsigned)data[8] << 8) | (unsigned)data[9];
    char maker[4] = {
        (char)(64 + ((code >> 10) & 31)),
        (char)(64 + ((code >> 5) & 31)),
        (char)(64 + (code & 31)),
        0
    };
    char model[32] = {0}, serial[32] = {0};
    for (size_t offset = 54; offset + 18 <= 126; offset += 18) {
        const unsigned char *block = data + offset;
        if (block[0] == 0 && block[1] == 0 && block[2] == 0 &&
            (block[3] == 0xfc || block[3] == 0xff)) {
            char raw[14];
            memcpy(raw, block + 5, 13);
            raw[13] = 0;
            trim_inplace(raw);
            if (block[3] == 0xfc) tam_monitor_clean(raw, model, sizeof(model));
            else tam_monitor_clean(raw, serial, sizeof(serial));
        }
    }
    char combined[160] = {0};
    snprintf(combined, sizeof(combined), "%s%s%s%s%s",
        maker,
        *model ? " " : "", model,
        *serial ? " " : "", serial);
    tam_monitor_clean(combined, out, cap);
}

static long long monotonic_ms(void)
{
    struct timespec ts = {0};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000LL + ts.tv_nsec / 1000000LL;
}

int tam_monitor_run_tool_timeout(const char *const *argv, int timeout_ms,
    char *out, size_t out_cap, char *err, size_t err_cap)
{
    if (out && out_cap) out[0] = 0;
    if (err && err_cap) err[0] = 0;
    if (!argv || !argv[0]) return -1;
    int out_pipe[2] = {-1, -1}, err_pipe[2] = {-1, -1};
    if (pipe2(out_pipe, O_CLOEXEC | O_NONBLOCK) < 0 ||
        pipe2(err_pipe, O_CLOEXEC | O_NONBLOCK) < 0) {
        if (out_pipe[0] >= 0) { close(out_pipe[0]); close(out_pipe[1]); }
        if (err && err_cap) snprintf(err, err_cap, "%s unavailable: %s", argv[0], strerror(errno));
        return -1;
    }
    pid_t pid = fork();
    if (pid < 0) {
        int saved = errno;
        close(out_pipe[0]); close(out_pipe[1]);
        close(err_pipe[0]); close(err_pipe[1]);
        if (err && err_cap) snprintf(err, err_cap, "%s unavailable: %s", argv[0], strerror(saved));
        return -1;
    }
    if (pid == 0) {
        setsid();
        int devnull = open("/dev/null", O_RDONLY);
        if (devnull >= 0) { dup2(devnull, STDIN_FILENO); close(devnull); }
        dup2(out_pipe[1], STDOUT_FILENO);
        dup2(err_pipe[1], STDERR_FILENO);
        close(out_pipe[0]); close(out_pipe[1]);
        close(err_pipe[0]); close(err_pipe[1]);
        execvp(argv[0], (char *const *)argv);
        dprintf(STDERR_FILENO, "%s unavailable: %s\n", argv[0], strerror(errno));
        _exit(127);
    }
    close(out_pipe[1]);
    close(err_pipe[1]);
    size_t out_len = 0, err_len = 0;
    char out_buf[4096] = {0}, err_buf[4096] = {0};
    long long deadline = monotonic_ms() + (timeout_ms > 0 ? timeout_ms : TAM_MONITOR_CALL_TIMEOUT_MS);
    bool timed_out = false;
    while (out_pipe[0] >= 0 || err_pipe[0] >= 0) {
        long long remaining = deadline - monotonic_ms();
        if (remaining <= 0) {
            timed_out = true;
            break;
        }
        struct pollfd fds[2] = {
            {.fd = out_pipe[0], .events = POLLIN},
            {.fd = err_pipe[0], .events = POLLIN}
        };
        int n = poll(fds, 2, (int)remaining);
        if (n < 0) {
            if (errno == EINTR) continue;
            break;
        }
        if (n == 0) {
            timed_out = true;
            break;
        }
        for (int i = 0; i < 2; ++i) {
            int *pfd = (i == 0) ? &out_pipe[0] : &err_pipe[0];
            char *buf = (i == 0) ? out_buf : err_buf;
            size_t *len = (i == 0) ? &out_len : &err_len;
            size_t cap = sizeof(out_buf) - 1;
            if (*pfd < 0 || !fds[i].revents) continue;
            char chunk[512];
            ssize_t got = read(*pfd, chunk, sizeof(chunk));
            if (got > 0) {
                size_t copy = (size_t)got;
                if (*len + copy > cap) copy = cap - *len;
                if (copy > 0) {
                    memcpy(buf + *len, chunk, copy);
                    *len += copy;
                    buf[*len] = 0;
                }
            } else if (got == 0 || (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)) {
                close(*pfd);
                *pfd = -1;
            }
        }
    }
    if (out_pipe[0] >= 0) close(out_pipe[0]);
    if (err_pipe[0] >= 0) close(err_pipe[0]);
    int status = 0;
    if (timed_out) {
        kill(-pid, SIGKILL);
        while (waitpid(pid, &status, 0) < 0 && errno == EINTR) {}
        if (err && err_cap) snprintf(err, err_cap, "%s timed out", argv[0]);
        return -1;
    }
    while (waitpid(pid, &status, 0) < 0) {
        if (errno != EINTR) break;
    }
    trim_inplace(out_buf);
    trim_inplace(err_buf);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        if (err && err_cap) {
            if (*err_buf) tam_monitor_clean(err_buf, err, err_cap);
            else snprintf(err, err_cap, "%s failed (device permission or hardware unavailable)", argv[0]);
        }
        return -1;
    }
    if (out && out_cap) snprintf(out, out_cap, "%s", out_buf);
    return 0;
}

static bool valid_connector_dir_name(const char *name, unsigned *card_out, char *conn_out, size_t conn_cap)
{
    if (strncmp(name, "card", 4) != 0 || !isdigit((unsigned char)name[4])) return false;
    const char *p = name + 4;
    unsigned long card = 0;
    while (isdigit((unsigned char)*p)) {
        card = card * 10 + (unsigned)(*p - '0');
        if (card >= 64) return false;
        ++p;
    }
    if (*p != '-') return false;
    ++p;
    size_t len = strlen(p);
    if (len < 1 || len > 64 || len >= conn_cap) return false;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)p[i];
        if (!(isalnum(c) || c == '.' || c == '_' || c == '-')) return false;
    }
    *card_out = (unsigned)card;
    snprintf(conn_out, conn_cap, "%s", p);
    return true;
}

static bool is_internal_panel(const char *connector)
{
    return !strncmp(connector, "eDP-", 4) ||
           !strncmp(connector, "LVDS-", 5) ||
           !strncmp(connector, "DSI-", 4);
}

static bool valid_backlight_name(const char *name)
{
    size_t len = strlen(name);
    if (len < 1 || len > 80) return false;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)name[i];
        if (!(isalnum(c) || c == '_' || c == '.' || c == ':' || c == '-')) return false;
    }
    return true;
}

static int cmp_str(const void *a, const void *b)
{
    return strcmp(*(const char *const *)a, *(const char *const *)b);
}

int tam_monitor_read_brightness(struct tam_monitor_info *m, char *err, size_t err_cap)
{
    if (!m) return -1;
    char value_str[128] = {0}, tool_err[160] = {0};
    if (!strcmp(m->brightness_backend, "ddc")) {
        const char *argv[] = {"tam-brightness-display-ddc", m->connector, NULL};
        if (tam_monitor_run_tool(argv, value_str, sizeof(value_str), tool_err, sizeof(tool_err)) < 0) {
            if (err && err_cap) snprintf(err, err_cap, "%s", tool_err);
            return -1;
        }
    } else if (!strcmp(m->brightness_backend, "backlight")) {
        const char *argv[] = {"tam-hw-display", NULL};
        char bl_name[128] = {0};
        if (tam_monitor_run_tool(argv, bl_name, sizeof(bl_name), tool_err, sizeof(tool_err)) < 0) {
            if (err && err_cap) snprintf(err, err_cap, "%s", tool_err);
            return -1;
        }
        char bl_dir[512];
        snprintf(bl_dir, sizeof(bl_dir), "%s/%s", tam_monitor_sysfs_backlight_path(), bl_name);
        struct stat st;
        if (!valid_backlight_name(bl_name) || stat(bl_dir, &st) < 0 || !S_ISDIR(st.st_mode)) {
            if (err && err_cap) snprintf(err, err_cap, "No supported internal backlight");
            return -1;
        }
        snprintf(m->backlight, sizeof(m->backlight), "%s", bl_name);
        char cur_path[600], max_path[600], cur_str[64], max_str[64];
        snprintf(cur_path, sizeof(cur_path), "%s/brightness", bl_dir);
        snprintf(max_path, sizeof(max_path), "%s/max_brightness", bl_dir);
        read_text_file(cur_path, cur_str, sizeof(cur_str));
        read_text_file(max_path, max_str, sizeof(max_str));
        char *end1 = NULL, *end2 = NULL;
        errno = 0;
        long current = strtol(cur_str, &end1, 10);
        long maximum = strtol(max_str, &end2, 10);
        if (errno || !*cur_str || *end1 || !*max_str || *end2 ||
            maximum <= 0 || current < 0 || current > maximum) {
            if (err && err_cap) snprintf(err, err_cap, "Invalid or unavailable backlight range");
            return -1;
        }
        int rounded = (int)lround((double)current * 100.0 / (double)maximum);
        snprintf(value_str, sizeof(value_str), "%d", rounded);
    } else {
        if (err && err_cap) snprintf(err, err_cap, "%s", m->brightness_detail);
        return -1;
    }
    char *end = NULL;
    errno = 0;
    long percent = strtol(value_str, &end, 10);
    if (errno || !*value_str || *end || percent < 0 || percent > 100) {
        if (err && err_cap) snprintf(err, err_cap, "Invalid brightness response");
        return -1;
    }
    m->brightness = (int)percent;
    snprintf(m->brightness_detail, sizeof(m->brightness_detail), "available");
    return (int)percent;
}

int tam_monitor_discover(bool probe, struct tam_monitor_info *out,
    size_t max_count, size_t *count_out, char *err, size_t err_cap)
{
    if (count_out) *count_out = 0;
    if (err && err_cap) err[0] = 0;
    const char *drm_root = tam_monitor_sysfs_drm_path();
    DIR *dir = opendir(drm_root);
    if (!dir) {
        if (err && err_cap) snprintf(err, err_cap, "Cannot open %s: %s", drm_root, strerror(errno));
        return -1;
    }
    char *names[128];
    size_t name_count = 0;
    struct dirent *de;
    while ((de = readdir(dir)) != NULL) {
        if (strncmp(de->d_name, "card", 4) != 0 || !strchr(de->d_name, '-')) continue;
        if (name_count < 128) {
            names[name_count] = strdup(de->d_name);
            if (names[name_count]) ++name_count;
        }
    }
    closedir(dir);
    qsort(names, name_count, sizeof(names[0]), cmp_str);

    size_t count = 0;
    for (size_t i = 0; i < name_count; ++i) {
        unsigned card = 0;
        char conn[64];
        char status_path[600];
        snprintf(status_path, sizeof(status_path), "%s/%s/status", drm_root, names[i]);
        if (valid_connector_dir_name(names[i], &card, conn, sizeof(conn)) &&
            access(status_path, F_OK) == 0) {
            if (count >= TAM_MONITOR_MAX_MONITORS || count >= max_count) {
                for (size_t j = i; j < name_count; ++j) free(names[j]);
                if (err && err_cap)
                    snprintf(err, err_cap, "More than %d connectors; refusing an incomplete hardware map",
                        TAM_MONITOR_MAX_MONITORS);
                return -1;
            }
            struct tam_monitor_info *m = &out[count++];
            memset(m, 0, sizeof(*m));
            snprintf(m->id, sizeof(m->id), "%s", names[i]);
            snprintf(m->connector, sizeof(m->connector), "%s", conn);
            m->card = card;
            m->brightness = -1;
            snprintf(m->brightness_detail, sizeof(m->brightness_detail), "not probed");
            char edid_path[600], enabled_path[600];
            snprintf(edid_path, sizeof(edid_path), "%s/%s/edid", drm_root, names[i]);
            snprintf(enabled_path, sizeof(enabled_path), "%s/%s/enabled", drm_root, names[i]);
            tam_monitor_edid_identity(edid_path, m->identity, sizeof(m->identity));
            read_text_file(status_path, m->connection, sizeof(m->connection));
            read_text_file(enabled_path, m->enabled, sizeof(m->enabled));
            if (!strcmp(m->connection, "connected")) {
                snprintf(m->power_detail, sizeof(m->power_detail),
                    "Targeted console blank/wake/keep via native DRM/KMS (requires foreground text VT)");
            } else {
                snprintf(m->power_detail, sizeof(m->power_detail),
                    "Individual power unavailable: connector not connected");
            }
            snprintf(m->layout_detail, sizeof(m->layout_detail),
                "Targeted console routing via libtam-display");
        }
        free(names[i]);
    }

    size_t internal_connected = 0;
    for (size_t i = 0; i < count; ++i) {
        if (!strcmp(out[i].connection, "connected") && is_internal_panel(out[i].connector))
            ++internal_connected;
    }

    for (size_t i = 0; i < count; ++i) {
        struct tam_monitor_info *m = &out[i];
        if (strcmp(m->connection, "connected") != 0) {
            snprintf(m->brightness_detail, sizeof(m->brightness_detail), "not connected");
            continue;
        }
        size_t same_conn = 0;
        for (size_t j = 0; j < count; ++j) {
            if (!strcmp(out[j].connection, "connected") && !strcmp(out[j].connector, m->connector))
                ++same_conn;
        }
        if (same_conn > 1) {
            snprintf(m->brightness_detail, sizeof(m->brightness_detail), "ambiguous connector across GPUs");
            continue;
        }
        if (is_internal_panel(m->connector)) {
            if (internal_connected != 1) {
                snprintf(m->brightness_detail, sizeof(m->brightness_detail),
                    "ambiguous internal panel/backlight mapping");
                continue;
            }
            snprintf(m->brightness_backend, sizeof(m->brightness_backend), "backlight");
        } else {
            snprintf(m->brightness_backend, sizeof(m->brightness_backend), "ddc");
        }
        if (probe) {
            char probe_err[160] = {0};
            if (tam_monitor_read_brightness(m, probe_err, sizeof(probe_err)) < 0)
                tam_monitor_clean(probe_err, m->brightness_detail, sizeof(m->brightness_detail));
        }
    }
    if (count_out) *count_out = count;
    return 0;
}

int tam_monitor_find_current(const char *name, struct tam_monitor_info *out,
    char *err, size_t err_cap)
{
    if (!name || !*name || !out) {
        if (err && err_cap) snprintf(err, err_cap, "Select one connected monitor by its full card/connector ID");
        return -1;
    }
    struct tam_monitor_info list[TAM_MONITOR_MAX_MONITORS];
    size_t count = 0;
    if (tam_monitor_discover(false, list, TAM_MONITOR_MAX_MONITORS, &count, err, err_cap) < 0)
        return -1;
    size_t matches = 0, matched_idx = 0;
    for (size_t i = 0; i < count; ++i) {
        if (!strcmp(list[i].id, name) || !strcmp(list[i].connector, name)) {
            matched_idx = i;
            ++matches;
        }
    }
    if (matches != 1) {
        if (err && err_cap) snprintf(err, err_cap, "Select one connected monitor by its full card/connector ID");
        return -1;
    }
    if (!list[matched_idx].brightness_backend[0]) {
        if (err && err_cap) snprintf(err, err_cap, "%s", list[matched_idx].brightness_detail);
        return -1;
    }
    *out = list[matched_idx];
    return 0;
}

int tam_monitor_set_brightness(const char *name, int percent,
    int *actual_out, char *err, size_t err_cap)
{
    if (percent < 1 || percent > 100) {
        if (err && err_cap)
            snprintf(err, err_cap, "Brightness must be 1-100%%; use blank to blank the console");
        return -1;
    }
    struct tam_monitor_info m;
    if (tam_monitor_find_current(name, &m, err, err_cap) < 0) return -1;
    if (tam_monitor_read_brightness(&m, err, err_cap) < 0) return -1;
    char pct_arg[32], tool_out[128], tool_err[160];
    snprintf(pct_arg, sizeof(pct_arg), "%d%%", percent);
    double tolerance = 1.0;
    if (!strcmp(m.brightness_backend, "ddc")) {
        const char *argv[] = {"tam-brightness-display-ddc", m.connector, pct_arg, NULL};
        if (tam_monitor_run_tool(argv, tool_out, sizeof(tool_out), tool_err, sizeof(tool_err)) < 0) {
            if (err && err_cap) snprintf(err, err_cap, "%s", tool_err);
            return -1;
        }
    } else {
        const char *argv[] = {"brightnessctl", "-d", m.backlight, "set", pct_arg, NULL};
        if (tam_monitor_run_tool(argv, tool_out, sizeof(tool_out), tool_err, sizeof(tool_err)) < 0) {
            if (err && err_cap) snprintf(err, err_cap, "%s", tool_err);
            return -1;
        }
        char max_path[600], max_str[64];
        snprintf(max_path, sizeof(max_path), "%s/%s/max_brightness",
            tam_monitor_sysfs_backlight_path(), m.backlight);
        read_text_file(max_path, max_str, sizeof(max_str));
        long maximum = strtol(max_str, NULL, 10);
        if (maximum > 0 && 100.0 / (double)maximum > 1.0)
            tolerance = 100.0 / (double)maximum;
    }
    int actual = tam_monitor_read_brightness(&m, err, err_cap);
    if (actual < 0) return -1;
    if (fabs((double)actual - (double)percent) > tolerance) {
        if (err && err_cap)
            snprintf(err, err_cap, "Brightness verification failed: requested %d%%, read %d%%",
                percent, actual);
        return -1;
    }
    if (actual_out) *actual_out = actual;
    return 0;
}

int tam_monitor_console_idle_seconds(int *seconds_out)
{
    if (!seconds_out) return -1;
    *seconds_out = -1;
    char buf[64];
    read_text_file(tam_monitor_consoleblank_path(), buf, sizeof(buf));
    if (!strcmp(buf, "unknown") || !*buf) return -1;
    char *end = NULL;
    errno = 0;
    long v = strtol(buf, &end, 10);
    if (errno || !*buf || *end || v < 0) return -1;
    *seconds_out = (int)v;
    return 0;
}
