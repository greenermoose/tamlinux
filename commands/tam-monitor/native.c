#define _POSIX_C_SOURCE 200809L
#include <tam_display.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Feasibility executable, deliberately not installed as the production command.
 * No open(), master acquisition, modeset, fork, terminal control or recovery yet. */
static void quoted(const char *s)
{
    putchar('"');
    for (; *s; ++s) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') { putchar('\\'); putchar(c); }
        else if (c < 32 || c > 126) printf("\\u%04x", c);
        else putchar(c);
    }
    putchar('"');
}

static int failure(bool json, int code, int syserr, const char *message)
{
    if (json) {
        printf("{\"ok\":false,\"code\":%d,\"errno\":%d,\"error\":", code, syserr);
        quoted(message); puts("}");
    } else fprintf(stderr, "tam-monitor: %s (code %d, errno %d)\n", message, code, syserr);
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

int main(int argc, char **argv)
{
    bool json = false;
    for (int i = 1; i < argc; ++i) if (!strcmp(argv[i], "--json")) json = true;
    if (argc == 2 && (!strcmp(argv[1], "--help") || !strcmp(argv[1], "-h"))) {
        puts("Usage: tam-monitor inspect --fd FD [--keep CONNECTOR] [--json]\n"
             "Experimental C feasibility tool; not installed by default.\n"
             "Inspect a DRM primary descriptor supplied by an authorized session owner.\n"
             "--keep analyzes routing only; it does not blank any monitor.\n"
             "Changes client capability visibility, never acquires master or modesets.\n"
             "Observations are transient and cannot restore displays.\n"
             "Existing list/brightness/blank/wake/idle remain in the installed command.");
        return 0;
    }
    if (argc < 2 || strcmp(argv[1], "inspect"))
        return failure(json, TAM_DISPLAY_INVALID, 0, "Expected inspect; see --help");
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
