#define _GNU_SOURCE
#include "native-console.h"
#include "native-hw.h"
#include <tam_display.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

#define CONSOLE_MAX_OUTPUTS 16
#define CONSOLE_MIN_PIXELS 64

struct console_output {
    char name[40];
    uint32_t width, height;
};

struct console_state {
    unsigned fb;
    char fb_name[64];
    int card;                 /* -1 when the framebuffer has no DRM card */
    bool visible_known;       /* current area read from the device */
    uint32_t width, height;   /* current console area */
    uint32_t max_width, max_height; /* framebuffer allocated at boot */
    const char *modes_from;   /* "drm", "sysfs" or "none" */
    size_t output_count;
    struct console_output outputs[CONSOLE_MAX_OUTPUTS];
};

static void json_string(const char *s)
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

static int fail(bool json, enum tam_display_result code, int syserr, const char *message)
{
    char cleaned[160];
    tam_monitor_clean(message, cleaned, sizeof(cleaned));
    if (json) {
        printf("{\"ok\":false,\"code\":%d,\"errno\":%d,\"error\":", code, syserr);
        json_string(cleaned);
        puts("}");
    } else fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", cleaned, code, syserr);
    return 1;
}

static bool read_small(const char *path, char *out, size_t cap)
{
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return false;
    ssize_t n = read(fd, out, cap - 1);
    close(fd);
    if (n < 0) return false;
    out[n] = '\0';
    char *nl = strchr(out, '\n');
    if (nl) *nl = '\0';
    return true;
}

static bool parse_pair(const char *s, char sep, uint32_t *a, uint32_t *b)
{
    char *end = NULL;
    if (!s || *s < '0' || *s > '9') return false;
    errno = 0;
    unsigned long x = strtoul(s, &end, 10);
    if (errno || !end || *end != sep || end[1] < '0' || end[1] > '9' || x > 65535) return false;
    const char *rest = end + 1;
    unsigned long y = strtoul(rest, &end, 10);
    if (errno || !end || (*end && *end != 'p' && *end != 'i' && *end != '-') || y > 65535) return false;
    *a = (uint32_t)x;
    *b = (uint32_t)y;
    return true;
}

static int find_card(const char *graphics, unsigned fb)
{
    char path[512];
    snprintf(path, sizeof(path), "%s/fb%u/device/drm", graphics, fb);
    DIR *d = opendir(path);
    if (!d) return -1;
    int card = -1;
    struct dirent *e;
    while ((e = readdir(d))) {
        unsigned n;
        char tail;
        if (sscanf(e->d_name, "card%u%c", &n, &tail) == 1 && n < 64) { card = (int)n; break; }
    }
    closedir(d);
    return card;
}

static void add_output(struct console_state *s, const char *name, uint32_t w, uint32_t h)
{
    if (s->output_count >= CONSOLE_MAX_OUTPUTS || !w || !h) return;
    struct console_output *o = &s->outputs[s->output_count++];
    snprintf(o->name, sizeof(o->name), "%s", name);
    o->width = w;
    o->height = h;
}

/* Current CRTC modes from DRM (the session's card ACL or root suffices; no
 * master needed). Falls back to each lit connector's preferred mode. */
static void read_outputs(struct console_state *s)
{
    s->modes_from = "none";
    if (s->card < 0) return;
    char path[512];
    snprintf(path, sizeof(path), "%s/dri/card%d", tam_monitor_dev_path(), s->card);
    int fd = open(path, O_RDWR | O_CLOEXEC);
    if (fd < 0) fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd >= 0) {
        struct tam_display_topology *t = NULL;
        struct tam_display_error e = {0};
        if (tam_display_inspect_fd(fd, &t, &e) == TAM_DISPLAY_OK && t) {
            for (size_t i = 0; i < t->connector_count; ++i) {
                const struct tam_display_connector *c = &t->connectors[i];
                if (c->connection != 1 || !c->crtc_id) continue;
                for (size_t j = 0; j < t->crtc_count; ++j) {
                    const struct tam_display_crtc *k = &t->crtcs[j];
                    if (k->object.id == c->crtc_id && k->mode_valid)
                        add_output(s, c->name, k->width, k->height);
                }
            }
            s->modes_from = "drm";
        }
        free(t);
        close(fd);
        if (!strcmp(s->modes_from, "drm")) return;
    }

    const char *drm = tam_monitor_sysfs_drm_path();
    DIR *d = opendir(drm);
    if (!d) return;
    char prefix[16];
    snprintf(prefix, sizeof(prefix), "card%d-", s->card);
    struct dirent *e;
    while ((e = readdir(d))) {
        if (strncmp(e->d_name, prefix, strlen(prefix)) || strlen(e->d_name) >= 64) continue;
        char status[32], enabled[32], mode[64];
        snprintf(path, sizeof(path), "%s/%s/status", drm, e->d_name);
        if (!read_small(path, status, sizeof(status)) || strcmp(status, "connected")) continue;
        snprintf(path, sizeof(path), "%s/%s/enabled", drm, e->d_name);
        if (!read_small(path, enabled, sizeof(enabled)) || strcmp(enabled, "enabled")) continue;
        snprintf(path, sizeof(path), "%s/%s/modes", drm, e->d_name);
        uint32_t w, h;
        if (read_small(path, mode, sizeof(mode)) && parse_pair(mode, 'x', &w, &h))
            add_output(s, e->d_name + strlen(prefix), w, h);
    }
    closedir(d);
    s->modes_from = "sysfs";
}

static int cmp_output(const void *a, const void *b)
{
    return strcmp(((const struct console_output *)a)->name, ((const struct console_output *)b)->name);
}

static enum tam_display_result read_state(unsigned fb, struct console_state *s, int *syserr, char *msg, size_t cap)
{
    memset(s, 0, sizeof(*s));
    s->fb = fb;
    const char *graphics = tam_monitor_sysfs_graphics_path();
    char path[512], text[64];
    snprintf(path, sizeof(path), "%s/fb%u/name", graphics, fb);
    if (!read_small(path, s->fb_name, sizeof(s->fb_name))) {
        *syserr = errno;
        snprintf(msg, cap, "No framebuffer fb%u", fb);
        return TAM_DISPLAY_NOT_FOUND;
    }
    snprintf(path, sizeof(path), "%s/fb%u/virtual_size", graphics, fb);
    if (!read_small(path, text, sizeof(text)) || !parse_pair(text, ',', &s->max_width, &s->max_height)) {
        *syserr = errno;
        snprintf(msg, cap, "Cannot read fb%u allocated size", fb);
        return TAM_DISPLAY_IO;
    }
    s->card = find_card(graphics, fb);

    snprintf(path, sizeof(path), "%s/fb%u", tam_monitor_dev_path(), fb);
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd >= 0) {
        struct fb_var_screeninfo var;
        if (tam_monitor_fb_get_var(fd, &var) == 0) {
            s->visible_known = true;
            s->width = var.xres;
            s->height = var.yres;
            if (var.xres_virtual && var.yres_virtual) {
                s->max_width = var.xres_virtual;
                s->max_height = var.yres_virtual;
            }
        }
        close(fd);
    }
    read_outputs(s);
    qsort(s->outputs, s->output_count, sizeof(s->outputs[0]), cmp_output);
    return TAM_DISPLAY_OK;
}

static const struct console_output *find_output(const struct console_state *s, const char *name)
{
    const char *dash = strchr(name, '-');
    if (!strncmp(name, "card", 4) && dash && dash[1]) name = dash + 1;
    for (size_t i = 0; i < s->output_count; ++i)
        if (!strcmp(s->outputs[i].name, name)) return &s->outputs[i];
    return NULL;
}

static const char *view_of(const struct console_state *s, const struct console_output *o)
{
    if (!s->visible_known) return "unknown";
    if (s->width == o->width && s->height == o->height) return "full";
    if (s->width <= o->width && s->height <= o->height) return "partial";
    return "cropped";
}

/* Text grid of the calling VT, when stdin is one (major 4, minor 1..63). */
static bool vt_grid(unsigned *cols, unsigned *rows)
{
    struct stat st;
    struct winsize ws;
    if (fstat(STDIN_FILENO, &st) || !S_ISCHR(st.st_mode) || major(st.st_rdev) != 4 ||
        minor(st.st_rdev) < 1 || minor(st.st_rdev) > 63) return false;
    if (ioctl(STDIN_FILENO, TIOCGWINSZ, &ws) || !ws.ws_col || !ws.ws_row) return false;
    *cols = ws.ws_col;
    *rows = ws.ws_row;
    return true;
}

static void print_json(const struct console_state *s, bool changed, bool verified)
{
    unsigned cols = 0, rows = 0;
    bool grid = vt_grid(&cols, &rows);
    printf("{\"ok\":true,\"fb\":%u,\"fb_name\":", s->fb);
    json_string(s->fb_name);
    printf(",\"card\":");
    if (s->card >= 0) printf("%d", s->card); else fputs("null", stdout);
    if (s->visible_known) printf(",\"width\":%u,\"height\":%u", s->width, s->height);
    else fputs(",\"width\":null,\"height\":null", stdout);
    printf(",\"max_width\":%u,\"max_height\":%u,\"changed\":%s,\"verified\":%s,\"text_grid\":",
        s->max_width, s->max_height, changed ? "true" : "false", verified ? "true" : "false");
    if (grid) printf("{\"cols\":%u,\"rows\":%u}", cols, rows); else fputs("null", stdout);
    printf(",\"modes_from\":");
    json_string(s->modes_from);
    printf(",\"outputs\":[");
    for (size_t i = 0; i < s->output_count; ++i) {
        const struct console_output *o = &s->outputs[i];
        printf("%s{\"connector\":", i ? "," : "");
        json_string(o->name);
        printf(",\"width\":%u,\"height\":%u,\"view\":", o->width, o->height);
        json_string(view_of(s, o));
        putchar('}');
    }
    puts("]}");
}

static void print_human(const struct console_state *s)
{
    printf("Console framebuffer fb%u (%s)", s->fb, s->fb_name);
    if (s->card >= 0) printf(" on card%d", s->card);
    putchar('\n');
    if (s->visible_known)
        printf("  Console area: %ux%u of %ux%u allocated at boot\n",
            s->width, s->height, s->max_width, s->max_height);
    else
        printf("  Console area: unknown without read access to %s/fb%u; %ux%u allocated at boot\n",
            tam_monitor_dev_path(), s->fb, s->max_width, s->max_height);
    unsigned cols, rows;
    if (vt_grid(&cols, &rows)) printf("  Text grid on this VT: %u columns x %u rows\n", cols, rows);
    if (!s->output_count) {
        puts("  Lit monitors: none found");
        return;
    }
    printf("  Lit monitors (%s):\n", !strcmp(s->modes_from, "drm") ? "current modes" : "preferred modes");
    for (size_t i = 0; i < s->output_count; ++i) {
        const struct console_output *o = &s->outputs[i];
        const char *view = view_of(s, o);
        printf("    %-10s %ux%u", o->name, o->width, o->height);
        if (!strcmp(view, "full")) puts("  console fills the screen");
        else if (!strcmp(view, "partial")) printf("  console uses the top-left %ux%u\n", s->width, s->height);
        else if (!strcmp(view, "cropped"))
            printf("  shows only the top-left %ux%u of the console\n",
                o->width < s->width ? o->width : s->width, o->height < s->height ? o->height : s->height);
        else putchar('\n');
    }
}

enum tam_monitor_console_set tam_monitor_console_set_area(unsigned fb, uint32_t width, uint32_t height,
    uint32_t *before_w, uint32_t *before_h, int *syserr)
{
    char path[512];
    snprintf(path, sizeof(path), "%s/fb%u", tam_monitor_dev_path(), fb);
    *syserr = 0;
    int fd = open(path, O_RDWR | O_CLOEXEC);
    if (fd < 0) { *syserr = errno; return TAM_MONITOR_CONSOLE_SET_OPEN; }
    struct fb_var_screeninfo var;
    if (tam_monitor_fb_get_var(fd, &var) != 0) {
        *syserr = errno;
        close(fd);
        return TAM_MONITOR_CONSOLE_SET_READ;
    }
    if (before_w) *before_w = var.xres;
    if (before_h) *before_h = var.yres;
    if (var.xres != width || var.yres != height) {
        var.xres = width;
        var.yres = height;
        var.xoffset = var.yoffset = 0;
        var.activate = FB_ACTIVATE_NOW | FB_ACTIVATE_ALL; /* resize every VT */
        if (tam_monitor_fb_put_var(fd, &var) != 0) {
            *syserr = errno;
            close(fd);
            return TAM_MONITOR_CONSOLE_SET_REFUSED;
        }
    }
    struct fb_var_screeninfo after;
    bool verified = tam_monitor_fb_get_var(fd, &after) == 0 && after.xres == width && after.yres == height;
    close(fd);
    return verified ? TAM_MONITOR_CONSOLE_SET_OK : TAM_MONITOR_CONSOLE_SET_UNVERIFIED;
}

bool tam_monitor_console_lit_area(int drm_fd, uint32_t *width, uint32_t *height)
{
    struct tam_display_topology *t = NULL;
    struct tam_display_error e = {0};
    if (tam_display_inspect_fd(drm_fd, &t, &e) != TAM_DISPLAY_OK || !t) { free(t); return false; }
    uint32_t w = UINT32_MAX, h = UINT32_MAX;
    for (size_t i = 0; i < t->connector_count; ++i) {
        const struct tam_display_connector *c = &t->connectors[i];
        if (c->connection != 1 || !c->crtc_id) continue;
        for (size_t j = 0; j < t->crtc_count; ++j) {
            const struct tam_display_crtc *k = &t->crtcs[j];
            if (k->object.id != c->crtc_id || !k->mode_valid || !k->width || !k->height) continue;
            if (k->width < w) w = k->width;
            if (k->height < h) h = k->height;
        }
    }
    free(t);
    if (w == UINT32_MAX || h == UINT32_MAX) return false;
    *width = w;
    *height = h;
    return true;
}

bool tam_monitor_console_writable(unsigned fb)
{
    char path[512];
    snprintf(path, sizeof(path), "%s/fb%u", tam_monitor_dev_path(), fb);
    return access(path, W_OK) == 0;
}

static void permission_hint(const char *verb_args)
{
    char self[512];
    ssize_t n = readlink("/proc/self/exe", self, sizeof(self) - 1);
    if (n <= 0) snprintf(self, sizeof(self), "tam-monitor");
    else self[n] = '\0';
    fprintf(stderr, "tam-monitor: run it as root from the text console:\n  sudo %s console-size %s\n",
        self, verb_args);
}

int tam_monitor_console_size(unsigned fb_index, enum tam_monitor_console_target target,
    const char *connector, unsigned width, unsigned height, bool json)
{
    struct console_state s;
    char msg[160] = {0};
    int syserr = 0;
    enum tam_display_result rc = read_state(fb_index, &s, &syserr, msg, sizeof(msg));
    if (rc != TAM_DISPLAY_OK) return fail(json, rc, syserr, msg);

    if (target == TAM_MONITOR_CONSOLE_SHOW) {
        if (json) print_json(&s, false, false); else print_human(&s);
        return ferror(stdout) ? 1 : 0;
    }

    char args[64];
    if (target == TAM_MONITOR_CONSOLE_MONITOR) {
        const struct console_output *o = find_output(&s, connector);
        if (!o) {
            snprintf(msg, sizeof(msg), "%s is not a lit monitor on card%d; run tam-monitor console-size to list them",
                connector, s.card);
            return fail(json, TAM_DISPLAY_NOT_FOUND, 0, msg);
        }
        width = o->width;
        height = o->height;
        snprintf(args, sizeof(args), "%s", connector);
    } else if (target == TAM_MONITOR_CONSOLE_ALL) {
        if (!s.output_count) return fail(json, TAM_DISPLAY_NOT_FOUND, 0, "No lit monitors found");
        width = height = UINT32_MAX;
        for (size_t i = 0; i < s.output_count; ++i) {
            if (s.outputs[i].width < width) width = s.outputs[i].width;
            if (s.outputs[i].height < height) height = s.outputs[i].height;
        }
        snprintf(args, sizeof(args), "--all");
    } else snprintf(args, sizeof(args), "%ux%u", width, height);

    if (width < CONSOLE_MIN_PIXELS || height < CONSOLE_MIN_PIXELS) {
        snprintf(msg, sizeof(msg), "Console area must be at least %ux%u", CONSOLE_MIN_PIXELS, CONSOLE_MIN_PIXELS);
        return fail(json, TAM_DISPLAY_INVALID, 0, msg);
    }
    if (width > s.max_width || height > s.max_height) {
        snprintf(msg, sizeof(msg), "%ux%u exceeds the %ux%u framebuffer allocated at boot; it cannot grow without a reboot",
            width, height, s.max_width, s.max_height);
        return fail(json, TAM_DISPLAY_LIMIT, 0, msg);
    }
    if (fb_index) snprintf(args + strlen(args), sizeof(args) - strlen(args), " --fb %u", fb_index);

    char path[512];
    snprintf(path, sizeof(path), "%s/fb%u", tam_monitor_dev_path(), fb_index);
    uint32_t before_w = 0, before_h = 0;
    int err = 0;
    enum tam_monitor_console_set set = tam_monitor_console_set_area(fb_index, width, height,
        &before_w, &before_h, &err);
    switch (set) {
    case TAM_MONITOR_CONSOLE_SET_OK:
    case TAM_MONITOR_CONSOLE_SET_UNVERIFIED:
        break;
    case TAM_MONITOR_CONSOLE_SET_OPEN:
        if (err == EACCES || err == EPERM) {
            snprintf(msg, sizeof(msg), "Changing the console size needs write access to %.80s (root or the video group)", path);
            fail(json, TAM_DISPLAY_PERMISSION, err, msg);
            if (!json) permission_hint(args);
            return 1;
        }
        snprintf(msg, sizeof(msg), "Cannot open %.80s: %.60s", path, strerror(err));
        return fail(json, TAM_DISPLAY_IO, err, msg);
    case TAM_MONITOR_CONSOLE_SET_READ:
        return fail(json, TAM_DISPLAY_IO, err, "Cannot read the console screen settings");
    case TAM_MONITOR_CONSOLE_SET_REFUSED:
        snprintf(msg, sizeof(msg), "The kernel refused a %ux%u console area: %s", width, height, strerror(err));
        return fail(json, err == EINVAL ? TAM_DISPLAY_UNSUPPORTED : TAM_DISPLAY_IO, err, msg);
    }
    bool changed = before_w != width || before_h != height;
    bool verified = set == TAM_MONITOR_CONSOLE_SET_OK;
    s.visible_known = true;
    s.width = width;
    s.height = height;
    if (json) {
        print_json(&s, changed, verified);
        return verified ? 0 : 1;
    }
    if (!changed) printf("Console area already %ux%u.\n", width, height);
    else printf("Console area set to %ux%u (%s; every VT, until reboot).\n", width, height,
        verified ? "verified" : "readback differs");
    print_human(&s);
    return verified && !ferror(stdout) ? 0 : 1;
}
