#ifndef TAM_MONITOR_NATIVE_HW_H
#define TAM_MONITOR_NATIVE_HW_H

#include <stdbool.h>
#include <stddef.h>

#define TAM_MONITOR_MAX_MONITORS 16
#define TAM_MONITOR_CALL_TIMEOUT_MS 6000

struct tam_monitor_info {
    char id[80];
    char connector[64];
    unsigned card;
    char identity[160];
    char connection[32];
    char enabled[32];
    int brightness; /* -1 when unknown / not probed */
    char brightness_backend[16];
    char brightness_detail[160];
    char backlight[80];
    char power_detail[160];
    char layout_detail[160];
};

void tam_monitor_clean(const char *src, char *dst, size_t cap);
void tam_monitor_edid_identity(const char *path, char *out, size_t cap);

const char *tam_monitor_sysfs_drm_path(void);
const char *tam_monitor_sysfs_backlight_path(void);
const char *tam_monitor_consoleblank_path(void);

int tam_monitor_run_tool_timeout(const char *const *argv, int timeout_ms,
    char *out, size_t out_cap, char *err, size_t err_cap);
int tam_monitor_run_tool(const char *const *argv,
    char *out, size_t out_cap, char *err, size_t err_cap);

int tam_monitor_discover(bool probe, struct tam_monitor_info *out,
    size_t max_count, size_t *count_out, char *err, size_t err_cap);
int tam_monitor_find_current(const char *name, struct tam_monitor_info *out,
    char *err, size_t err_cap);
int tam_monitor_read_brightness(struct tam_monitor_info *m,
    char *err, size_t err_cap);
int tam_monitor_set_brightness(const char *name, int percent,
    int *actual_out, char *err, size_t err_cap);
int tam_monitor_console_idle_seconds(int *seconds_out);

#endif
