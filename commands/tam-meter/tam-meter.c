#define _POSIX_C_SOURCE 200809L

#include "live.h"
#include "report.h"
#include "sensors.h"
#include "stats.h"
#include "version.h"

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/utsname.h>

static void safe_strcpy(char *dest, const char *src, size_t dest_size)
{
    if (!dest || dest_size == 0) return;
    if (!src) { dest[0] = '\0'; return; }
    size_t len = strlen(src);
    if (len >= dest_size) len = dest_size - 1;
    memcpy(dest, src, len);
    dest[len] = '\0';
}

static void print_usage(FILE *f)
{
    fprintf(f,
        "Usage: tam-meter <command> [options]\n\n"
        "Commands:\n"
        "  reading   Take a D170/D190 candidate test energy reading\n"
        "  now       Sample current power, temperature, and wakeups\n"
        "  top       Interactive full-screen monitor\n\n"
        "Options for reading:\n"
        "  --settle SECONDS    Settle time before sampling (default: 360)\n"
        "  --minutes MINUTES   Duration of measurement window (default: 10)\n"
        "  --interval SECONDS  Sample interval (default: 2)\n"
        "  --json              Output structured JSON\n\n"
        "Options for now:\n"
        "  --json              Output structured JSON\n\n"
        "Options for top:\n"
        "  --interval SECONDS  Refresh interval (default: 2)\n\n"
        "General:\n"
        "  -v, --version       Show version\n"
        "  -h, --help          Show this help\n");
}

static void precise_sleep(double seconds)
{
    if (seconds <= 0.0) return;
    struct timespec req;
    req.tv_sec = (time_t)seconds;
    req.tv_nsec = (long)((seconds - (double)req.tv_sec) * 1e9);
    nanosleep(&req, NULL);
}

typedef struct {
    char name[64];
    unsigned long long diff_ticks;
} proc_diff_item_t;

static int compare_proc_diff_items(const void *a, const void *b)
{
    const proc_diff_item_t *ia = (const proc_diff_item_t *)a;
    const proc_diff_item_t *ib = (const proc_diff_item_t *)b;
    if (ia->diff_ticks > ib->diff_ticks) return -1;
    if (ia->diff_ticks < ib->diff_ticks) return 1;
    return 0;
}

static int do_reading(const tam_meter_sensors_t *sensors, int settle, double minutes, double interval, bool json)
{
    tam_str_t disp_start = NULL;
    tam_meter_read_displays(sensors, &disp_start);

    time_t raw_t = time(NULL);
    struct tm *tm_info = localtime(&raw_t);
    char when_buf[64];
    strftime(when_buf, sizeof(when_buf), "%Y-%m-%d %H:%M %Z", tm_info);

    if (settle > 0) {
        precise_sleep((double)settle);
    }

    tam_meter_stat_t stat_start;
    tam_meter_read_stat(sensors, &stat_start);

    tam_meter_ticks_t ticks_start = {0, 0, 0};
    tam_meter_read_ticks(sensors, &ticks_start);

    double self_start = tam_meter_read_self_cpu_seconds(sensors);

    size_t est_samples = (size_t)((minutes * 60.0) / interval) + 10;
    if (est_samples < 16) est_samples = 16;
    double *power_samples = malloc(est_samples * sizeof(double));
    double *temp_samples = malloc(est_samples * sizeof(double));
    size_t sample_count = 0;
    size_t temp_count = 0;

    double end_time = 0.0;
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    double start_mono = (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
    end_time = start_mono + (minutes * 60.0);

    while (1) {
        clock_gettime(CLOCK_MONOTONIC, &ts);
        double now_mono = (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
        if (now_mono >= end_time) break;

        double pw = 0.0;
        if (tam_meter_read_power_w(sensors, &pw) == 0) {
            if (sample_count < est_samples) {
                power_samples[sample_count++] = pw;
            }
        }

        double tc = 0.0;
        if (tam_meter_read_temp_c(sensors, &tc) == 0) {
            if (temp_count < est_samples) {
                temp_samples[temp_count++] = tc;
            }
        }

        precise_sleep(interval);
    }

    tam_meter_stat_t stat_end;
    tam_meter_read_stat(sensors, &stat_end);

    tam_meter_ticks_t ticks_end = {0, 0, 0};
    tam_meter_read_ticks(sensors, &ticks_end);

    double self_end = tam_meter_read_self_cpu_seconds(sensors);

    tam_str_t disp_end = NULL;
    tam_meter_read_displays(sensors, &disp_end);

    tam_meter_report_data_t rep;
    memset(&rep, 0, sizeof(rep));

    safe_strcpy(rep.when_str, when_buf, sizeof(rep.when_str));
    rep.settle_seconds = settle;
    rep.minutes = minutes;
    rep.tool_cpu_seconds = (self_end >= self_start) ? (self_end - self_start) : 0.0;

    tam_meter_read_boot_id(sensors, rep.boot_id, sizeof(rep.boot_id));
    tam_meter_read_tamlinux_version(rep.tamlinux_version, sizeof(rep.tamlinux_version));

    struct utsname un;
    if (uname(&un) == 0) {
        safe_strcpy(rep.kernel_release, un.release, sizeof(rep.kernel_release));
    } else {
        safe_strcpy(rep.kernel_release, "unknown", sizeof(rep.kernel_release));
    }

    /* Power stats */
    if (sample_count > 0) {
        rep.has_power = true;
        tam_meter_calc_stats(power_samples, sample_count, &rep.power_stats);
    }
    free(power_samples);

    /* Temp stats */
    if (temp_count > 0) {
        rep.has_temp = true;
        tam_meter_calc_stats(temp_samples, temp_count, &rep.temp_stats);
    }
    free(temp_samples);

    /* Wakeups */
    double duration_secs = minutes * 60.0;
    if (duration_secs <= 0) duration_secs = 1.0;

    unsigned long long intr_diff = (stat_end.intr > stat_start.intr) ? (stat_end.intr - stat_start.intr) : 0;
    unsigned long long ctxt_diff = (stat_end.ctxt > stat_start.ctxt) ? (stat_end.ctxt - stat_start.ctxt) : 0;
    rep.interrupts_per_sec = (double)intr_diff / duration_secs;
    rep.context_switches_per_sec = (double)ctxt_diff / duration_secs;

    unsigned long long total_delta = (stat_end.total > stat_start.total) ? (stat_end.total - stat_start.total) : 1;
    unsigned long long busy_delta = (stat_end.busy > stat_start.busy) ? (stat_end.busy - stat_start.busy) : 0;
    rep.cpu_busy_percent = 100.0 * (double)busy_delta / (double)total_delta;

    /* Top processes */
    long hz = sysconf(_SC_CLK_TCK);
    if (hz <= 0) hz = 100;

    proc_diff_item_t *diff_items = calloc(ticks_end.count, sizeof(proc_diff_item_t));
    size_t diff_count = 0;

    for (size_t i = 0; i < ticks_end.count; i++) {
        int pid = ticks_end.items[i].pid;
        unsigned long long end_t = ticks_end.items[i].ticks;
        unsigned long long start_t = 0;
        bool found = false;

        for (size_t j = 0; j < ticks_start.count; j++) {
            if (ticks_start.items[j].pid == pid) {
                start_t = ticks_start.items[j].ticks;
                found = true;
                break;
            }
        }

        if (found && end_t > start_t) {
            safe_strcpy(diff_items[diff_count].name, ticks_end.items[i].comm, sizeof(diff_items[diff_count].name));
            diff_items[diff_count].diff_ticks = end_t - start_t;
            diff_count++;
        }
    }

    qsort(diff_items, diff_count, sizeof(proc_diff_item_t), compare_proc_diff_items);

    rep.top_proc_count = (diff_count < 3) ? diff_count : 3;
    for (size_t i = 0; i < rep.top_proc_count; i++) {
        safe_strcpy(rep.top_procs[i].name, diff_items[i].name, sizeof(rep.top_procs[i].name));
        rep.top_procs[i].cpu_seconds = (double)diff_items[i].diff_ticks / (double)hz;
    }
    free(diff_items);

    tam_meter_free_ticks(&ticks_start);
    tam_meter_free_ticks(&ticks_end);

    safe_strcpy(rep.displays_start, disp_start ? disp_start : "unknown", sizeof(rep.displays_start));
    safe_strcpy(rep.displays_end, disp_end ? disp_end : "unknown", sizeof(rep.displays_end));
    if (disp_start) tam_str_free(disp_start);
    if (disp_end) tam_str_free(disp_end);

    tam_meter_read_meminfo(sensors, &rep.avail_gib, &rep.swap_used_gib);
    rep.rapl_readable = sensors->rapl_readable;
    safe_strcpy(rep.power_source, sensors->power_source, sizeof(rep.power_source));
    safe_strcpy(rep.temp_source, sensors->temp_source, sizeof(rep.temp_source));

    tam_str_t out = NULL;
    if (json) {
        tam_meter_format_json(&rep, &out);
    } else {
        tam_meter_format_markdown(&rep, &out);
    }

    if (out) {
        printf("%s", out);
        tam_str_free(out);
    }

    return 0;
}

static int do_now(const tam_meter_sensors_t *sensors, bool json)
{
    tam_meter_stat_t s0, s1;
    tam_meter_read_stat(sensors, &s0);
    double p0 = 0.0, t0 = 0.0;
    tam_meter_read_power_w(sensors, &p0);
    tam_meter_read_temp_c(sensors, &t0);

    precise_sleep(1.0);

    tam_meter_read_stat(sensors, &s1);
    double p1 = 0.0, t1 = 0.0;
    tam_meter_read_power_w(sensors, &p1);
    tam_meter_read_temp_c(sensors, &t1);

    unsigned long long total_d = (s1.total > s0.total) ? (s1.total - s0.total) : 1;
    unsigned long long busy_d = (s1.busy > s0.busy) ? (s1.busy - s0.busy) : 0;
    double busy_pct = 100.0 * (double)busy_d / (double)total_d;

    double intr_s = (double)(s1.intr - s0.intr);
    double ctxt_s = (double)(s1.ctxt - s0.ctxt);

    double power_val = (p1 > 0.0) ? p1 : p0;
    double temp_val = (t1 > 0.0) ? t1 : t0;

    if (json) {
        tam_str_t j = tam_str_new("{\n");
        j = tam_str_cat(j, "  \"schema\": 1,\n");
        j = tam_str_cat_printf(j, "  \"tool\": \"tam-meter %s\",\n", TAM_METER_VERSION);
        if (sensors->power_available) {
            j = tam_str_cat_printf(j, "  \"power_w\": %.2f,\n", power_val);
        } else {
            j = tam_str_cat(j, "  \"power_w\": null,\n");
        }
        if (sensors->temp_available) {
            j = tam_str_cat_printf(j, "  \"temp_c\": %.2f,\n", temp_val);
        } else {
            j = tam_str_cat(j, "  \"temp_c\": null,\n");
        }
        j = tam_str_cat_printf(j, "  \"cpu_busy_percent\": %.2f,\n", busy_pct);
        j = tam_str_cat_printf(j, "  \"interrupts_per_sec\": %.1f,\n", intr_s);
        j = tam_str_cat_printf(j, "  \"context_switches_per_sec\": %.1f\n", ctxt_s);
        j = tam_str_cat(j, "}\n");
        printf("%s", j);
        tam_str_free(j);
    } else {
        printf("APU power: ");
        if (sensors->power_available) {
            printf("%.1f W", power_val);
        } else {
            printf("unavailable");
        }
        printf(" | CPU temp: ");
        if (sensors->temp_available) {
            printf("%.1f °C", temp_val);
        } else {
            printf("unavailable");
        }
        printf(" | CPU busy: %.1f%% | Wakeups: %.0f int/s, %.0f ctxt/s\n", busy_pct, intr_s, ctxt_s);
    }

    return 0;
}

int main(int argc, char **argv)
{
    if (tam_bundle_guard(NULL)) {
        fputs("Tamlinux is switching versions or needs recovery; use tam-bundle status from the console.\n", stderr);
        return 1;
    }
    if (argc < 2) {
        print_usage(stderr);
        return 1;
    }

    if (strcmp(argv[1], "--version") == 0 || strcmp(argv[1], "-v") == 0) {
        printf("%s\n", TAM_METER_VERSION);
        return 0;
    }
    if (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
        print_usage(stdout);
        return 0;
    }

    const char *cmd = argv[1];

    tam_meter_sensors_t sensors;
    tam_meter_init_sensors(&sensors, NULL, NULL);

    if (strcmp(cmd, "reading") == 0) {
        int settle = 360;
        double minutes = 10.0;
        double interval = 2.0;
        bool json = false;

        static struct option long_opts[] = {
            {"settle", required_argument, 0, 's'},
            {"minutes", required_argument, 0, 'm'},
            {"interval", required_argument, 0, 'i'},
            {"json", no_argument, 0, 'j'},
            {"help", no_argument, 0, 'h'},
            {0, 0, 0, 0}
        };

        optind = 2;
        int opt;
        while ((opt = getopt_long(argc, argv, "s:m:i:jh", long_opts, NULL)) != -1) {
            switch (opt) {
                case 's': settle = atoi(optarg); break;
                case 'm': minutes = atof(optarg); break;
                case 'i': interval = atof(optarg); break;
                case 'j': json = true; break;
                case 'h': print_usage(stdout); return 0;
                default:
                    print_usage(stderr);
                    return 1;
            }
        }
        if (minutes <= 0.0) minutes = 0.01;
        if (interval <= 0.0) interval = 0.5;

        return do_reading(&sensors, settle, minutes, interval, json);
    } else if (strcmp(cmd, "now") == 0) {
        bool json = false;
        static struct option long_opts[] = {
            {"json", no_argument, 0, 'j'},
            {"help", no_argument, 0, 'h'},
            {0, 0, 0, 0}
        };
        optind = 2;
        int opt;
        while ((opt = getopt_long(argc, argv, "jh", long_opts, NULL)) != -1) {
            switch (opt) {
                case 'j': json = true; break;
                case 'h': print_usage(stdout); return 0;
                default:
                    print_usage(stderr);
                    return 1;
            }
        }
        return do_now(&sensors, json);
    } else if (strcmp(cmd, "top") == 0) {
        double interval = 2.0;
        static struct option long_opts[] = {
            {"interval", required_argument, 0, 'i'},
            {"help", no_argument, 0, 'h'},
            {0, 0, 0, 0}
        };
        optind = 2;
        int opt;
        while ((opt = getopt_long(argc, argv, "i:h", long_opts, NULL)) != -1) {
            switch (opt) {
                case 'i': interval = atof(optarg); break;
                case 'h': print_usage(stdout); return 0;
                default:
                    print_usage(stderr);
                    return 1;
            }
        }
        if (interval < 0.2) interval = 0.2;
        return tam_meter_run_top(&sensors, interval);
    }

    fprintf(stderr, "tam-meter: unknown command '%s'\n", cmd);
    print_usage(stderr);
    return 1;
}
