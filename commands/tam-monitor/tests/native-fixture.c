#include <tam_display.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

/* Linked only into the test executable; never an environment hook in product. */
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
