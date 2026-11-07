#define _POSIX_C_SOURCE 200809L

#include "report.h"
#include "version.h"

#include <stdio.h>
#include <string.h>

void tam_meter_format_markdown(const tam_meter_report_data_t *data, tam_str_t *out)
{
    if (!data || !out) return;
    *out = tam_str_new("### Energy reading (D170)\n\n");

    /* When line */
    if (data->settle_seconds > 0) {
        *out = tam_str_cat_printf(*out,
            "- **When:** %s, %g minutes after %d minutes of settling; boot `%s`, Tamlinux %s, kernel %s.\n",
            data->when_str, data->minutes, data->settle_seconds / 60,
            data->boot_id, data->tamlinux_version, data->kernel_release);
    } else {
        *out = tam_str_cat_printf(*out,
            "- **When:** %s, %g minutes (settling skipped); boot `%s`, Tamlinux %s, kernel %s.\n",
            data->when_str, data->minutes,
            data->boot_id, data->tamlinux_version, data->kernel_release);
    }

    /* Tool line */
    *out = tam_str_cat_printf(*out,
        "- **Tool:** tam-meter %s (used %.2f s CPU while measuring).\n",
        TAM_METER_VERSION, data->tool_cpu_seconds);

    /* Power line */
    if (data->has_power) {
        const char *psrc = (data->power_source[0] && strcmp(data->power_source, "amdgpu PPT") != 0)
            ? data->power_source : "amdgpu PPT";
        *out = tam_str_cat_printf(*out,
            "- **APU power (%s):** mean %.1f W, median %.1f W, range %.1f–%.1f W (%zu samples).\n",
            psrc, data->power_stats.mean, data->power_stats.median,
            data->power_stats.min, data->power_stats.max,
            data->power_stats.count);
    } else {
        *out = tam_str_cat(*out, "- **APU power (amdgpu PPT):** unavailable.\n");
    }

    /* Temp line */
    if (data->has_temp) {
        *out = tam_str_cat_printf(*out,
            "- **CPU temperature (Tctl):** mean %.1f °C, range %.1f–%.1f °C.\n",
            data->temp_stats.mean, data->temp_stats.min, data->temp_stats.max);
    }

    /* Wakeups line */
    *out = tam_str_cat_printf(*out,
        "- **Wakeups:** %.0f interrupts/s, %.0f context switches/s; CPU busy %.1f%%.\n",
        data->interrupts_per_sec, data->context_switches_per_sec, data->cpu_busy_percent);

    /* Busiest processes */
    *out = tam_str_cat(*out, "- **Busiest processes:** ");
    if (data->top_proc_count == 0) {
        *out = tam_str_cat(*out, "none.\n");
    } else {
        for (size_t i = 0; i < data->top_proc_count; i++) {
            if (i > 0) *out = tam_str_cat(*out, ", ");
            *out = tam_str_cat_printf(*out, "%s %.1f s", data->top_procs[i].name, data->top_procs[i].cpu_seconds);
        }
        *out = tam_str_cat(*out, ".\n");
    }

    /* Displays */
    *out = tam_str_cat_printf(*out,
        "- **Displays:** start %s; end %s.\n",
        data->displays_start[0] ? data->displays_start : "unknown",
        data->displays_end[0] ? data->displays_end : "unknown");

    /* Memory */
    *out = tam_str_cat_printf(*out,
        "- **Memory:** %.1f GiB available, %.1f GiB swap used.\n",
        data->avail_gib, data->swap_used_gib);

    /* Not measured */
    *out = tam_str_cat(*out,
        "- **Not measured:** wall power (no meter yet);");
    if (!data->rapl_readable) {
        *out = tam_str_cat(*out, " RAPL package energy (root-only);");
    }
    *out = tam_str_cat(*out, " the APU figure excludes RAM, SSD, network, the power supply's losses and the monitors.\n");
}

void tam_meter_format_json(const tam_meter_report_data_t *data, tam_str_t *out)
{
    if (!data || !out) return;
    *out = tam_str_new("{\n");
    *out = tam_str_cat(*out, "  \"schema\": 1,\n");
    *out = tam_str_cat_printf(*out, "  \"tool\": \"tam-meter %s\",\n", TAM_METER_VERSION);
    *out = tam_str_cat_printf(*out, "  \"tool_cpu_seconds\": %.3f,\n", data->tool_cpu_seconds);
    *out = tam_str_cat(*out, "  \"when\": \"");
    *out = tam_str_cat_json(*out, data->when_str);
    *out = tam_str_cat(*out, "\",\n");
    *out = tam_str_cat_printf(*out, "  \"settle_seconds\": %d,\n", data->settle_seconds);
    *out = tam_str_cat_printf(*out, "  \"duration_minutes\": %g,\n", data->minutes);
    *out = tam_str_cat_printf(*out, "  \"boot_id\": \"%s\",\n", data->boot_id);
    *out = tam_str_cat_printf(*out, "  \"tamlinux_version\": \"%s\",\n", data->tamlinux_version);
    *out = tam_str_cat_printf(*out, "  \"kernel\": \"%s\",\n", data->kernel_release);

    /* Power */
    if (data->has_power) {
        const char *psrc = (data->power_source[0] && strcmp(data->power_source, "amdgpu PPT") != 0)
            ? data->power_source : "amdgpu PPT";
        *out = tam_str_cat(*out, "  \"power\": {\n");
        *out = tam_str_cat(*out, "    \"available\": true,\n");
        *out = tam_str_cat_printf(*out, "    \"sensor\": \"%s\",\n", psrc);
        *out = tam_str_cat_printf(*out, "    \"mean_w\": %.2f,\n", data->power_stats.mean);
        *out = tam_str_cat_printf(*out, "    \"median_w\": %.2f,\n", data->power_stats.median);
        *out = tam_str_cat_printf(*out, "    \"min_w\": %.2f,\n", data->power_stats.min);
        *out = tam_str_cat_printf(*out, "    \"max_w\": %.2f,\n", data->power_stats.max);
        *out = tam_str_cat_printf(*out, "    \"samples\": %zu\n", data->power_stats.count);
        *out = tam_str_cat(*out, "  },\n");
    } else {
        *out = tam_str_cat(*out, "  \"power\": null,\n");
    }

    /* Temperature */
    *out = tam_str_cat(*out, "  \"temperature\": {\n");
    *out = tam_str_cat_printf(*out, "    \"available\": %s,\n", data->has_temp ? "true" : "false");
    if (data->has_temp) {
        const char *tsrc = (data->temp_source[0] && strcmp(data->temp_source, "k10temp Tctl") != 0)
            ? data->temp_source : "k10temp Tctl";
        *out = tam_str_cat_printf(*out, "    \"sensor\": \"%s\",\n", tsrc);
        *out = tam_str_cat_printf(*out, "    \"mean_c\": %.2f,\n", data->temp_stats.mean);
        *out = tam_str_cat_printf(*out, "    \"min_c\": %.2f,\n", data->temp_stats.min);
        *out = tam_str_cat_printf(*out, "    \"max_c\": %.2f\n", data->temp_stats.max);
    } else {
        *out = tam_str_cat(*out, "    \"sensor\": null\n");
    }
    *out = tam_str_cat(*out, "  },\n");

    /* Wakeups */
    *out = tam_str_cat(*out, "  \"wakeups\": {\n");
    *out = tam_str_cat_printf(*out, "    \"interrupts_per_sec\": %.1f,\n", data->interrupts_per_sec);
    *out = tam_str_cat_printf(*out, "    \"context_switches_per_sec\": %.1f,\n", data->context_switches_per_sec);
    *out = tam_str_cat_printf(*out, "    \"cpu_busy_percent\": %.2f\n", data->cpu_busy_percent);
    *out = tam_str_cat(*out, "  },\n");

    /* Busiest processes */
    *out = tam_str_cat(*out, "  \"busiest_processes\": [\n");
    for (size_t i = 0; i < data->top_proc_count; i++) {
        *out = tam_str_cat(*out, "    {\"name\": \"");
        *out = tam_str_cat_json(*out, data->top_procs[i].name);
        *out = tam_str_cat_printf(*out, "\", \"cpu_seconds\": %.2f}%s\n",
            data->top_procs[i].cpu_seconds,
            (i + 1 < data->top_proc_count) ? "," : "");
    }
    *out = tam_str_cat(*out, "  ],\n");

    /* Displays */
    *out = tam_str_cat(*out, "  \"displays\": {\n");
    *out = tam_str_cat(*out, "    \"start\": \"");
    *out = tam_str_cat_json(*out, data->displays_start);
    *out = tam_str_cat(*out, "\",\n    \"end\": \"");
    *out = tam_str_cat_json(*out, data->displays_end);
    *out = tam_str_cat(*out, "\"\n  },\n");

    /* Memory */
    *out = tam_str_cat(*out, "  \"memory\": {\n");
    *out = tam_str_cat_printf(*out, "    \"available_gib\": %.2f,\n", data->avail_gib);
    *out = tam_str_cat_printf(*out, "    \"swap_used_gib\": %.2f\n", data->swap_used_gib);
    *out = tam_str_cat(*out, "  }\n");

    *out = tam_str_cat(*out, "}\n");
}
