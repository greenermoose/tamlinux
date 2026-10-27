#define _GNU_SOURCE
#include <tam_display.h>
#include <tam_vt.h>
#include "native-hw.h"
#include "native-preview.h"
#include "native-tui.h"
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char *tam_monitor_sysfs_drm_path(void) { return "/sys/class/drm"; }
const char *tam_monitor_sysfs_backlight_path(void) { return "/sys/class/backlight"; }
const char *tam_monitor_consoleblank_path(void) { return "/sys/module/kernel/parameters/consoleblank"; }

int tam_monitor_run_tool(const char *const *argv,
    char *out, size_t out_cap, char *err, size_t err_cap)
{
    return tam_monitor_run_tool_timeout(argv, TAM_MONITOR_CALL_TIMEOUT_MS, out, out_cap, err, err_cap);
}

static void quoted(const char *s)
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

static int failure(bool json, int code, int syserr, const char *message)
{
    char cleaned[160];
    tam_monitor_clean(message ? message : "Unknown error", cleaned, sizeof(cleaned));
    if (json) {
        printf("{\"ok\":false,\"code\":%d,\"errno\":%d,\"error\":", code, syserr);
        quoted(cleaned); puts("}");
    } else fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", cleaned, code, syserr);
    return 1;
}

static void ids(const uint32_t *values, size_t count)
{
    putchar('[');
    for (size_t i = 0; i < count; ++i) printf("%s%u", i ? "," : "", values[i]);
    putchar(']');
}

static void object(const struct tam_display_object *o)
{
    printf("{\"id\":%u,\"properties\":[", o->id);
    for (size_t j = 0; j < o->property_count; ++j) {
        const struct tam_display_property *p = &o->properties[j];
        printf("%s{\"id\":%u,\"name\":", j ? "," : "", p->id);
        quoted(p->name);
        /* Decimal strings preserve full u64 property values in JSON clients. */
        printf(",\"value\":\"%llu\",\"flags\":%u}", (unsigned long long)p->value, p->flags);
    }
    printf("]}");
}

static void output_json(const struct tam_display_topology *t, const struct tam_display_plan *plan)
{
    printf("{\"ok\":true,\"read_only\":true,\"restorable\":false,\"display_api\":");
    quoted(TAM_DISPLAY_API_VERSION);
    printf(",\"driver\":"); quoted(t->driver);
    printf(",\"connectors\":[");
    for (size_t i = 0; i < t->connector_count; ++i) {
        const struct tam_display_connector *c = &t->connectors[i];
        printf("%s{\"name\":", i ? "," : ""); quoted(c->name);
        printf(",\"connection\":%u,\"encoder\":%u,\"crtc\":%u,\"object\":",
            c->connection, c->encoder_id, c->crtc_id);
        object(&c->object); putchar('}');
    }
    printf("],\"crtcs\":[");
    for (size_t i = 0; i < t->crtc_count; ++i) {
        const struct tam_display_crtc *c = &t->crtcs[i];
        printf("%s{\"framebuffer\":%u,\"mode_valid\":%s,\"x\":%u,\"y\":%u,\"width\":%u,\"height\":%u,\"object\":",
            i ? "," : "", c->framebuffer_id, c->mode_valid ? "true" : "false",
            c->x, c->y, c->width, c->height);
        object(&c->object); putchar('}');
    }
    printf("],\"planes\":[");
    for (size_t i = 0; i < t->plane_count; ++i) {
        const struct tam_display_plane *p = &t->planes[i];
        printf("%s{\"crtc\":%u,\"framebuffer\":%u,\"possible_crtcs\":%u,\"object\":",
            i ? "," : "", p->crtc_id, p->framebuffer_id, p->possible_crtcs);
        object(&p->object); putchar('}');
    }
    putchar(']');
    if (plan) {
        printf(",\"analysis\":{\"validated_by_kernel\":false,\"keep\":%u,\"detach\":", plan->keep_connector);
        ids(plan->detach, plan->detach_count);
        printf(",\"disable_crtcs\":"); ids(plan->disable_crtcs, plan->disable_crtc_count);
        printf(",\"disable_planes\":"); ids(plan->disable_planes, plan->disable_plane_count);
        putchar('}');
    }
    puts("}");
}

static void print_list_json(const struct tam_monitor_info *monitors, size_t count)
{
    puts("[");
    for (size_t i = 0; i < count; ++i) {
        const struct tam_monitor_info *m = &monitors[i];
        printf("  {\n    \"id\": "); quoted(m->id);
        printf(",\n    \"connector\": "); quoted(m->connector);
        printf(",\n    \"identity\": "); quoted(m->identity);
        printf(",\n    \"connection\": "); quoted(m->connection);
        printf(",\n    \"enabled\": "); quoted(m->enabled);
        printf(",\n    \"brightness\": ");
        if (m->brightness >= 0) printf("%d", m->brightness);
        else fputs("null", stdout);
        printf(",\n    \"brightness_backend\": "); quoted(m->brightness_backend);
        printf(",\n    \"brightness_detail\": "); quoted(m->brightness_detail);
        printf(",\n    \"backlight\": "); quoted(m->backlight);
        printf(",\n    \"power_detail\": "); quoted(m->power_detail);
        printf(",\n    \"layout_detail\": "); quoted(m->layout_detail);
        printf("\n  }%s\n", (i + 1 < count) ? "," : "");
    }
    puts("]");
}

static bool parse_bounded_uint(const char *value, unsigned min_v, unsigned max_v, unsigned *out)
{
    if (!value || !*value || *value < '0' || *value > '9') return false;
    char *end = NULL;
    errno = 0;
    unsigned long n = strtoul(value, &end, 10);
    if (errno || !end || *end || n < min_v || n > max_v) return false;
    *out = (unsigned)n;
    return true;
}

static void print_help(void)
{
    puts("Usage: tam-monitor [COMMAND ...]\n"
         "Monitor information, brightness and targeted Linux text-console display control.\n"
         "Run without arguments on a terminal to open the interactive TUI.\n\n"
         "Commands:\n"
         "  list [--json] [--no-probe]\n"
         "  brightness MONITOR [1..100]\n"
         "  keep CONNECTOR --shell [--card N] [--json]\n"
         "  keep CONNECTOR --seconds 1..60 [--card N] [--json]\n"
         "  blank [--monitor CONNECTOR ...] [--seconds 1..60] [--card N] [--json]\n"
         "  wake [--monitor CONNECTOR | --all] [--json]\n"
         "  idle 0..60\n"
         "  preview --card N --keep CONNECTOR --seconds 1..60 [--json]\n"
         "  inspect --fd FD [--keep CONNECTOR] [--json]\n\n"
         "Lifetime and safety:\n"
         "  Targeted console selection requires an owned foreground Linux text VT and active\n"
         "  local login session. A separate recovery owner holds VT handoff and DRM state\n"
         "  and restores surviving console outputs on exit, shell completion, timeout,\n"
         "  signals, hotplug or VT switch.\n"
         "  inspect --keep analyzes routing only; it does not blank any monitor.");
}

int main(int argc, char **argv)
{
    if (argc >= 2 && !strcmp(argv[1], "__guard"))
        return tam_monitor_guard_entry(argc - 2, argv + 2);

    bool json = false;
    for (int i = 1; i < argc; ++i)
        if (!strcmp(argv[i], "--json")) json = true;

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) {
            print_help();
            return 0;
        }
    }

    if (argc == 1)
        return tam_monitor_tui();

    const char *cmd = argv[1];

    if (!strcmp(cmd, "list")) {
        bool no_probe = false;
        for (int i = 2; i < argc; ++i) {
            if (!strcmp(argv[i], "--json")) continue;
            if (!strcmp(argv[i], "--no-probe")) no_probe = true;
            else return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown list option");
        }
        struct tam_monitor_info monitors[TAM_MONITOR_MAX_MONITORS];
        size_t count = 0;
        char err[160] = {0};
        if (tam_monitor_discover(!no_probe, monitors, TAM_MONITOR_MAX_MONITORS, &count, err, sizeof(err)) < 0)
            return failure(json, TAM_DISPLAY_IO, errno, err);
        if (json) {
            print_list_json(monitors, count);
        } else {
            for (size_t i = 0; i < count; ++i) {
                const struct tam_monitor_info *m = &monitors[i];
                printf("%s: %s; %s\n", m->id, m->connection, m->identity);
                if (m->brightness >= 0)
                    printf("  Brightness: %d%%; %s\n", m->brightness, m->power_detail);
                else
                    printf("  Brightness: %s; %s\n", m->brightness_detail, m->power_detail);
            }
        }
        return ferror(stdout) ? 1 : 0;
    }

    if (!strcmp(cmd, "brightness")) {
        if (argc < 3 || argc > 4)
            return failure(json, TAM_DISPLAY_INVALID, 0, "Usage: tam-monitor brightness MONITOR [1..100]");
        const char *mon_name = argv[2];
        char err[160] = {0};
        if (argc == 3) {
            struct tam_monitor_info m;
            if (tam_monitor_find_current(mon_name, &m, err, sizeof(err)) < 0)
                return failure(json, TAM_DISPLAY_INVALID, 0, err);
            int val = tam_monitor_read_brightness(&m, err, sizeof(err));
            if (val < 0) return failure(json, TAM_DISPLAY_IO, 0, err);
            printf("%d\n", val);
            return 0;
        }
        unsigned pct = 0;
        if (!parse_bounded_uint(argv[3], 1, 100, &pct))
            return failure(json, TAM_DISPLAY_INVALID, 0, "Brightness must be an integer 1-100");
        int actual = 0;
        if (tam_monitor_set_brightness(mon_name, (int)pct, &actual, err, sizeof(err)) < 0)
            return failure(json, TAM_DISPLAY_INVALID, 0, err);
        printf("%d\n", actual);
        return 0;
    }

    if (!strcmp(cmd, "idle")) {
        if (argc != 3)
            return failure(json, TAM_DISPLAY_INVALID, 0, "Usage: tam-monitor idle 0..60");
        unsigned minutes = 0;
        if (!parse_bounded_uint(argv[2], 0, 60, &minutes))
            return failure(json, TAM_DISPLAY_INVALID, 0, "Idle interval must be 0-60 minutes");
        struct tam_vt vt = {.fd = -1};
        struct tam_display_error e = {0};
        if (tam_vt_open(&vt, &e) != TAM_DISPLAY_OK)
            return failure(json, e.code, e.system_errno, e.message);
        bool verified = false;
        enum tam_display_result rc = tam_vt_idle_path(&vt, minutes,
            tam_monitor_consoleblank_path(), &verified, &e);
        tam_vt_close(&vt);
        if (rc != TAM_DISPLAY_OK)
            return failure(json, e.code, e.system_errno, e.message);
        printf("Console idle interval %s: %u minutes (0 = off; runtime only)\n",
            verified ? "verified" : "requested (readback unavailable)", minutes);
        return 0;
    }

    if (!strcmp(cmd, "keep")) {
        const char *target = NULL;
        unsigned card = 64, seconds = 0;
        bool shell = false;
        for (int i = 2; i < argc; ++i) {
            if (!strcmp(argv[i], "--json")) continue;
            if (!strcmp(argv[i], "--shell")) {
                if (shell) return failure(json, TAM_DISPLAY_INVALID, 0, "Repeated --shell option");
                shell = true;
            } else if (!strcmp(argv[i], "--card") && i + 1 < argc && card == 64) {
                if (!parse_bounded_uint(argv[++i], 0, 63, &card))
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid card number");
            } else if (!strcmp(argv[i], "--seconds") && i + 1 < argc && seconds == 0) {
                if (!parse_bounded_uint(argv[++i], 1, 60, &seconds))
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid bounded duration (1..60)");
            } else if (!strcmp(argv[i], "--keep") && i + 1 < argc && !target) {
                target = argv[++i];
            } else if (argv[i][0] != '-' && !target) {
                target = argv[i];
            } else {
                return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown, repeated or incomplete keep option");
            }
        }
        if (!target || !*target || strlen(target) >= 64)
            return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid or missing connector name for keep");
        if (shell && seconds > 0)
            return failure(json, TAM_DISPLAY_INVALID, 0, "Specify either --shell or --seconds, not both");
        return tam_monitor_keep(card, target, shell, seconds, json);
    }

    if (!strcmp(cmd, "blank")) {
        const char *monitors[TAM_DISPLAY_MAX_OBJECTS];
        size_t mon_count = 0;
        unsigned seconds = 15, card = 64;
        bool seconds_explicit = false;
        for (int i = 2; i < argc; ++i) {
            if (!strcmp(argv[i], "--json")) continue;
            if (!strcmp(argv[i], "--monitor") && i + 1 < argc) {
                const char *m = argv[++i];
                if (!*m || strlen(m) >= 64 || mon_count >= TAM_DISPLAY_MAX_OBJECTS)
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid connector name for blank");
                monitors[mon_count++] = m;
            } else if (!strcmp(argv[i], "--seconds") && i + 1 < argc && !seconds_explicit) {
                if (!parse_bounded_uint(argv[++i], 1, 60, &seconds))
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Blank duration must be 1-60 seconds");
                seconds_explicit = true;
            } else if (!strcmp(argv[i], "--card") && i + 1 < argc && card == 64) {
                if (!parse_bounded_uint(argv[++i], 0, 63, &card))
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid card number");
            } else {
                return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown, repeated or incomplete blank option");
            }
        }
        if (mon_count > 0) {
            return tam_monitor_blank_monitors(card, monitors, mon_count, seconds, seconds_explicit, json);
        }
        if (card != 64)
            return failure(json, TAM_DISPLAY_INVALID, 0, "--card requires --monitor");
        char err[160] = {0};
        if (!json) {
            printf("Blanking console; press a key to wake (maximum %us).\n", seconds);
            fflush(stdout);
        }
        int rc = tam_monitor_blank_console(seconds, NULL, err, sizeof(err));
        if (rc == 130) return 130;
        if (rc != 0) return failure(json, TAM_DISPLAY_IO, 0, err);
        if (json) puts("{\"ok\":true,\"code\":0,\"errno\":0}");
        return 0;
    }

    if (!strcmp(cmd, "wake")) {
        const char *monitor = NULL;
        bool all = false;
        for (int i = 2; i < argc; ++i) {
            if (!strcmp(argv[i], "--json")) continue;
            if (!strcmp(argv[i], "--all")) {
                if (all) return failure(json, TAM_DISPLAY_INVALID, 0, "Repeated --all option");
                all = true;
            } else if (!strcmp(argv[i], "--monitor") && i + 1 < argc && !monitor) {
                monitor = argv[++i];
                if (!*monitor || strlen(monitor) >= 64)
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid connector name for wake");
            } else if (argv[i][0] != '-' && !monitor) {
                monitor = argv[i];
                if (!*monitor || strlen(monitor) >= 64)
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid connector name for wake");
            } else {
                return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown, repeated or incomplete wake option");
            }
        }
        if (monitor && all)
            return failure(json, TAM_DISPLAY_INVALID, 0, "Specify either --monitor or --all, not both");
        return tam_monitor_wake(monitor, all, json);
    }

    if (!strcmp(cmd, "preview")) {
        unsigned card = 64, seconds = 0;
        const char *target = NULL;
        for (int i = 2; i < argc; ++i) {
            if (!strcmp(argv[i], "--json")) continue;
            const char *option = argv[i];
            if (i + 1 == argc) return failure(json, TAM_DISPLAY_INVALID, 0, "Incomplete preview option");
            const char *value = argv[++i];
            if (!strcmp(option, "--keep") && !target) {
                if (!*value || strlen(value) >= 40) return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid connector name");
                target = value;
            } else if ((!strcmp(option, "--card") && card == 64) ||
                       (!strcmp(option, "--seconds") && seconds == 0)) {
                char *end;
                errno = 0;
                unsigned long n = strtoul(value, &end, 10);
                if (errno || !*value || *end || *value < '0' || *value > '9' ||
                    (!strcmp(option, "--card") ? n >= 64 : n < 1 || n > 60))
                    return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid card or bounded duration");
                if (!strcmp(option, "--card")) card = (unsigned)n;
                else seconds = (unsigned)n;
            } else return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown or repeated preview option");
        }
        if (card == 64 || !seconds || !target)
            return failure(json, TAM_DISPLAY_INVALID, 0, "Preview requires --card, --keep and --seconds");
        return tam_monitor_preview(card, target, seconds, json);
    }

    if (strcmp(cmd, "inspect") != 0)
        return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown subcommand; see --help");

    int fd = -1;
    const char *keep = NULL;
    for (int i = 2; i < argc; ++i) {
        if (!strcmp(argv[i], "--json")) continue;
        if (!strcmp(argv[i], "--fd") && i + 1 < argc && fd == -1) {
            const char *value = argv[++i];
            char *end;
            errno = 0;
            long n = strtol(value, &end, 10);
            if (errno || !*value || *end || n < 0 || n > INT_MAX)
                return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid descriptor number");
            fd = (int)n;
        } else if (!strcmp(argv[i], "--keep") && i + 1 < argc && !keep) {
            keep = argv[++i];
            if (!*keep || strlen(keep) >= sizeof(((struct tam_display_connector *)0)->name))
                return failure(json, TAM_DISPLAY_INVALID, 0, "Invalid connector name");
        } else return failure(json, TAM_DISPLAY_INVALID, 0, "Unknown, repeated or incomplete option");
    }
    if (fd < 0) return failure(json, TAM_DISPLAY_INVALID, 0, "An authorized --fd is required");
    struct tam_display_error error;
    struct tam_display_topology *t = NULL;
    enum tam_display_result rc = tam_display_inspect_fd(fd, &t, &error);
    if (rc) return failure(json, rc, error.system_errno, error.message);
    struct tam_display_plan plan;
    if (keep) {
        rc = tam_display_plan_keep(t, keep, &plan, &error);
        if (rc) { free(t); return failure(json, rc, error.system_errno, error.message); }
    }
    if (json) output_json(t, keep ? &plan : NULL);
    else {
        printf("Driver: %s; display API %s\n", t->driver, TAM_DISPLAY_API_VERSION);
        puts("Read-only observation; not a restorable snapshot.");
        for (size_t i = 0; i < t->connector_count; ++i) {
            const struct tam_display_connector *c = &t->connectors[i];
            printf("%s: connector %u, connection %u, encoder %u, CRTC %u\n",
                c->name, c->object.id, c->connection, c->encoder_id, c->crtc_id);
        }
        if (keep) printf("Analysis: retain %s; detach %zu connectors, disable %zu CRTCs and %zu planes.\n"
            "Not tested by the kernel; no display state changed.\n", keep,
            plan.detach_count, plan.disable_crtc_count, plan.disable_plane_count);
    }
    free(t);
    return ferror(stdout) ? 1 : 0;
}
