#ifndef TAM_MONITOR_NATIVE_PREVIEW_H
#define TAM_MONITOR_NATIVE_PREVIEW_H

#include <stdbool.h>
#include <stddef.h>
#include <termios.h>
#include <tam_display.h>

int tam_monitor_preview(unsigned card, const char *keep, unsigned seconds, int json);

int tam_monitor_keep(unsigned card, const char *keep, bool shell,
    unsigned seconds, int json);

int tam_monitor_blank_monitors(unsigned card, const char *const *connectors,
    size_t count, unsigned seconds, bool seconds_explicit, int json);

int tam_monitor_wake(const char *connector, bool all, int json);

int tam_monitor_blank_console(unsigned seconds,
    const struct termios *restore_termios, char *err, size_t err_cap);

int tam_monitor_supervisor_request(unsigned vt_number, const char *request,
    struct tam_display_error *e);

int tam_monitor_guard_entry(int argc, char **argv);

#endif
