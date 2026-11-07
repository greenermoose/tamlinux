#ifndef SENSORS_H
#define SENSORS_H

#include <stdbool.h>
#include <stddef.h>
#include <limits.h>
#include <tam.h>

typedef struct {
    char power_path[PATH_MAX];
    char power_current_path[PATH_MAX];
    char power_voltage_path[PATH_MAX];
    bool power_is_battery_calc;
    char temp_path[PATH_MAX];
    bool power_available;
    bool temp_available;
    bool rapl_readable;
    char power_source[32];
    char temp_source[32];
    char sysfs_root[PATH_MAX];
    char proc_root[PATH_MAX];
} tam_meter_sensors_t;

typedef struct {
    unsigned long long busy;
    unsigned long long total;
    unsigned long long intr;
    unsigned long long ctxt;
} tam_meter_stat_t;

typedef struct {
    int pid;
    char comm[64];
    unsigned long long ticks;
} tam_meter_proc_tick_t;

typedef struct {
    tam_meter_proc_tick_t *items;
    size_t count;
    size_t capacity;
} tam_meter_ticks_t;

int    tam_meter_init_sensors(tam_meter_sensors_t *s, const char *sysfs_override, const char *proc_override);
int    tam_meter_read_power_w(const tam_meter_sensors_t *s, double *out_w);
int    tam_meter_read_temp_c(const tam_meter_sensors_t *s, double *out_c);
int    tam_meter_read_stat(const tam_meter_sensors_t *s, tam_meter_stat_t *out);
int    tam_meter_read_ticks(const tam_meter_sensors_t *s, tam_meter_ticks_t *out);
void   tam_meter_free_ticks(tam_meter_ticks_t *ticks);
int    tam_meter_read_displays(const tam_meter_sensors_t *s, tam_str_t *out);
int    tam_meter_read_meminfo(const tam_meter_sensors_t *s, double *out_avail_gib, double *out_swap_used_gib);
int    tam_meter_read_boot_id(const tam_meter_sensors_t *s, char *out_boot_id, size_t max_len);
int    tam_meter_read_tamlinux_version(char *out_version, size_t max_len);
double tam_meter_read_self_cpu_seconds(const tam_meter_sensors_t *s);

#endif
