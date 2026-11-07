#ifndef REPORT_H
#define REPORT_H

#include "sensors.h"
#include "stats.h"
#include <tam.h>

typedef struct {
    char name[64];
    double cpu_seconds;
} tam_meter_top_proc_t;

typedef struct {
    char when_str[64];
    int settle_seconds;
    double minutes;
    char boot_id[32];
    char tamlinux_version[64];
    char kernel_release[64];
    double tool_cpu_seconds;

    tam_meter_stats_t power_stats;
    bool has_power;

    tam_meter_stats_t temp_stats;
    bool has_temp;

    double interrupts_per_sec;
    double context_switches_per_sec;
    double cpu_busy_percent;

    tam_meter_top_proc_t top_procs[3];
    size_t top_proc_count;

    char displays_start[256];
    char displays_end[256];

    double avail_gib;
    double swap_used_gib;
    bool rapl_readable;
    char power_source[32];
    char temp_source[32];
} tam_meter_report_data_t;

void tam_meter_format_markdown(const tam_meter_report_data_t *data, tam_str_t *out);
void tam_meter_format_json(const tam_meter_report_data_t *data, tam_str_t *out);

#endif
