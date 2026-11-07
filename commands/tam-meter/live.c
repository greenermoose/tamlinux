#define _POSIX_C_SOURCE 200809L

#include "live.h"
#include "version.h"

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>
#include <sys/ioctl.h>

static volatile sig_atomic_t g_stop = 0;
static struct termios g_orig_termios;
static bool g_raw_enabled = false;

static void handle_signal(int sig)
{
    (void)sig;
    g_stop = 1;
}

static void restore_terminal(void)
{
    if (g_raw_enabled) {
        /* Show cursor, exit alternate screen */
        const char *exit_seq = "\033[?25h\033[?1049l";
        (void)write(STDOUT_FILENO, exit_seq, strlen(exit_seq));
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &g_orig_termios);
        g_raw_enabled = false;
    }
}

static int enable_raw_mode(void)
{
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO)) return -1;
    if (tcgetattr(STDIN_FILENO, &g_orig_termios) == -1) return -1;

    struct termios raw = g_orig_termios;
    raw.c_iflag &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
    raw.c_oflag &= ~(OPOST);
    raw.c_cflag |= (CS8);
    raw.c_lflag &= ~(ECHO | ICANON | IEXTEN | ISIG);
    raw.c_cc[VMIN] = 0;
    raw.c_cc[VTIME] = 0;

    if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == -1) return -1;
    g_raw_enabled = true;
    atexit(restore_terminal);

    /* Enter alternate screen, hide cursor */
    const char *enter_seq = "\033[?1049h\033[?25l";
    if (write(STDOUT_FILENO, enter_seq, strlen(enter_seq)) < 0) {}

    return 0;
}

static const char *sparkline_char(double val, double min_v, double max_v)
{
    static const char *bars[] = { " ", "▂", "▃", "▄", "▅", "▆", "▇", "█" };
    if (max_v <= min_v) return bars[3];
    double norm = (val - min_v) / (max_v - min_v);
    if (norm < 0.0) norm = 0.0;
    if (norm > 1.0) norm = 1.0;
    int idx = (int)(norm * 7.0 + 0.5);
    if (idx < 0) idx = 0;
    if (idx > 7) idx = 7;
    return bars[idx];
}

typedef struct {
    int pid;
    char comm[64];
    double cpu_pct;
    double total_time_s;
} proc_diff_t;

static int compare_proc_diff(const void *a, const void *b)
{
    const proc_diff_t *pa = (const proc_diff_t *)a;
    const proc_diff_t *pb = (const proc_diff_t *)b;
    if (pa->cpu_pct > pb->cpu_pct) return -1;
    if (pa->cpu_pct < pb->cpu_pct) return 1;
    return 0;
}

int tam_meter_run_top(const tam_meter_sensors_t *sensors, double interval_seconds)
{
    if (enable_raw_mode() != 0) {
        fprintf(stderr, "tam-meter: top mode requires an interactive terminal\n");
        return 1;
    }

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handle_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    #define MAX_HISTORY 60
    double power_history[MAX_HISTORY];
    size_t hist_count = 0;

    tam_meter_stat_t prev_stat;
    tam_meter_ticks_t prev_ticks = {0, 0, 0};
    tam_meter_read_stat(sensors, &prev_stat);
    tam_meter_read_ticks(sensors, &prev_ticks);

    long hz = sysconf(_SC_CLK_TCK);
    if (hz <= 0) hz = 100;

    while (!g_stop) {
        double power_w = 0.0;
        bool has_power = (tam_meter_read_power_w(sensors, &power_w) == 0);
        double temp_c = 0.0;
        bool has_temp = (tam_meter_read_temp_c(sensors, &temp_c) == 0);

        tam_meter_stat_t curr_stat;
        tam_meter_ticks_t curr_ticks = {0, 0, 0};
        tam_meter_read_stat(sensors, &curr_stat);
        tam_meter_read_ticks(sensors, &curr_ticks);

        double avail_gib = 0.0, swap_gib = 0.0;
        tam_meter_read_meminfo(sensors, &avail_gib, &swap_gib);

        tam_str_t displays = NULL;
        tam_meter_read_displays(sensors, &displays);

        if (has_power) {
            if (hist_count < MAX_HISTORY) {
                power_history[hist_count++] = power_w;
            } else {
                memmove(power_history, power_history + 1, (MAX_HISTORY - 1) * sizeof(double));
                power_history[MAX_HISTORY - 1] = power_w;
            }
        }

        /* Calculate CPU stats */
        unsigned long long total_delta = (curr_stat.total > prev_stat.total) ? (curr_stat.total - prev_stat.total) : 1;
        unsigned long long busy_delta = (curr_stat.busy > prev_stat.busy) ? (curr_stat.busy - prev_stat.busy) : 0;
        double cpu_busy_pct = 100.0 * (double)busy_delta / (double)total_delta;

        double intr_rate = (double)(curr_stat.intr - prev_stat.intr) / interval_seconds;
        double ctxt_rate = (double)(curr_stat.ctxt - prev_stat.ctxt) / interval_seconds;
        if (intr_rate < 0) intr_rate = 0;
        if (ctxt_rate < 0) ctxt_rate = 0;

        /* Calculate process differences */
        proc_diff_t *diffs = calloc(curr_ticks.count, sizeof(proc_diff_t));
        size_t diff_count = 0;

        for (size_t i = 0; i < curr_ticks.count; i++) {
            int pid = curr_ticks.items[i].pid;
            unsigned long long cur_t = curr_ticks.items[i].ticks;
            unsigned long long prev_t = 0;

            for (size_t j = 0; j < prev_ticks.count; j++) {
                if (prev_ticks.items[j].pid == pid) {
                    prev_t = prev_ticks.items[j].ticks;
                    break;
                }
            }

            unsigned long long d_ticks = (cur_t > prev_t) ? (cur_t - prev_t) : 0;
            double pct = 100.0 * ((double)d_ticks / (double)hz) / interval_seconds;

            diffs[diff_count].pid = pid;
            strncpy(diffs[diff_count].comm, curr_ticks.items[i].comm, sizeof(diffs[diff_count].comm) - 1);
            diffs[diff_count].cpu_pct = pct;
            diffs[diff_count].total_time_s = (double)cur_t / (double)hz;
            diff_count++;
        }

        qsort(diffs, diff_count, sizeof(proc_diff_t), compare_proc_diff);

        /* Render */
        tam_str_t scr = tam_str_new("\033[H");
        scr = tam_str_cat_printf(scr, "\033[1;36mtam-meter top v%s\033[0m  |  Interval: \033[1m%.1fs\033[0m  |  q: quit  +/-: interval\033[K\r\n\r\n",
            TAM_METER_VERSION, interval_seconds);

        scr = tam_str_cat(scr, "  Power: ");
        if (has_power) {
            scr = tam_str_cat_printf(scr, "\033[1;32m%5.1f W\033[0m (PPT)  ", power_w);
        } else {
            scr = tam_str_cat(scr, "\033[90munavailable\033[0m  ");
        }

        scr = tam_str_cat(scr, "  Temp: ");
        if (has_temp) {
            scr = tam_str_cat_printf(scr, "\033[1;33m%4.1f °C\033[0m (Tctl)  ", temp_c);
        } else {
            scr = tam_str_cat(scr, "\033[90munavailable\033[0m  ");
        }

        scr = tam_str_cat_printf(scr, "  CPU Busy: \033[1m%5.1f%%\033[0m  Mem: \033[1m%.1f GiB\033[0m avail\033[K\r\n",
            cpu_busy_pct, avail_gib);

        /* Sparkline */
        scr = tam_str_cat(scr, "  Power history: [");
        if (hist_count > 0) {
            double p_min = power_history[0], p_max = power_history[0];
            for (size_t i = 1; i < hist_count; i++) {
                if (power_history[i] < p_min) p_min = power_history[i];
                if (power_history[i] > p_max) p_max = power_history[i];
            }
            for (size_t i = 0; i < hist_count; i++) {
                scr = tam_str_cat(scr, sparkline_char(power_history[i], p_min, p_max));
            }
        }
        scr = tam_str_cat(scr, "]\033[K\r\n");

        scr = tam_str_cat_printf(scr, "  Wakeups: \033[1m%.0f\033[0m intr/s, \033[1m%.0f\033[0m ctxt/s  |  Displays: %s\033[K\r\n",
            intr_rate, ctxt_rate, displays ? displays : "unknown");

        scr = tam_str_cat(scr, "────────────────────────────────────────────────────────────────────────────\033[K\r\n");
        scr = tam_str_cat(scr, "\033[1m  PID    COMMAND                   CPU %     TIME\033[0m\033[K\r\n");

        size_t show_count = (diff_count < 12) ? diff_count : 12;
        for (size_t i = 0; i < show_count; i++) {
            scr = tam_str_cat_printf(scr, "%6d   %-24.24s  %6.1f%%   %7.1f s\033[K\r\n",
                diffs[i].pid, diffs[i].comm, diffs[i].cpu_pct, diffs[i].total_time_s);
        }
        scr = tam_str_cat(scr, "\033[J");

        (void)write(STDOUT_FILENO, scr, tam_str_len(scr));
        tam_str_free(scr);
        if (displays) tam_str_free(displays);
        free(diffs);

        /* Move current to prev */
        prev_stat = curr_stat;
        tam_meter_free_ticks(&prev_ticks);
        prev_ticks = curr_ticks;

        /* Non-blocking input loop with poll */
        struct pollfd pfd = { STDIN_FILENO, POLLIN, 0 };
        int ms_left = (int)(interval_seconds * 1000.0);
        while (ms_left > 0 && !g_stop) {
            int chunk = (ms_left > 100) ? 100 : ms_left;
            int ret = poll(&pfd, 1, chunk);
            if (ret > 0 && (pfd.revents & POLLIN)) {
                char c = 0;
                if (read(STDIN_FILENO, &c, 1) > 0) {
                    if (c == 'q' || c == 'Q' || c == 27) { /* 27 is ESC */
                        g_stop = 1;
                        break;
                    } else if (c == '+' || c == '=') {
                        interval_seconds -= 0.5;
                        if (interval_seconds < 0.5) interval_seconds = 0.5;
                        break;
                    } else if (c == '-' || c == '_') {
                        interval_seconds += 0.5;
                        if (interval_seconds > 10.0) interval_seconds = 10.0;
                        break;
                    }
                }
            }
            ms_left -= chunk;
        }
    }

    tam_meter_free_ticks(&prev_ticks);
    restore_terminal();
    return 0;
}
