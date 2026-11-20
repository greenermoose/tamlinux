#define _POSIX_C_SOURCE 200809L

#include "report.h"
#include "sensors.h"
#include "stats.h"
#include "version.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_failures = 0;

static void expect(int cond, const char *msg)
{
    if (!cond) {
        fprintf(stderr, "FAIL: %s\n", msg);
        g_failures++;
    }
}

int main(void)
{
    tam_meter_sensors_t s;
    const char *fix_sys = "tests/fixtures/sysfs";
    const char *fix_proc = "tests/fixtures/procfs";

    expect(tam_meter_init_sensors(&s, fix_sys, fix_proc) == 0, "init sensors with fixtures");
    expect(s.power_available, "power sensor available");
    expect(s.temp_available, "temp sensor available");

    double pw = 0.0;
    expect(tam_meter_read_power_w(&s, &pw) == 0, "read power");
    expect(fabs(pw - 4.12) < 0.001, "power matches fixture 4.12 W");

    double tc = 0.0;
    expect(tam_meter_read_temp_c(&s, &tc) == 0, "read temp");
    expect(fabs(tc - 38.5) < 0.001, "temp matches fixture 38.5 C");

    tam_meter_stat_t st;
    expect(tam_meter_read_stat(&s, &st) == 0, "read stat");
    expect(st.total == 244800, "stat total");
    expect(st.busy == 4300, "stat busy (total - idle - io)");
    expect(st.intr == 1234567, "stat intr");
    expect(st.ctxt == 2345678, "stat ctxt");

    tam_meter_ticks_t tk;
    expect(tam_meter_read_ticks(&s, &tk) == 0, "read ticks");
    expect(tk.count >= 2, "read at least 2 pids");
    bool found_systemd = false, found_quickshell = false;
    for (size_t i = 0; i < tk.count; i++) {
        if (tk.items[i].pid == 1 && strcmp(tk.items[i].comm, "systemd") == 0) {
            found_systemd = true;
            expect(tk.items[i].ticks == 400, "pid 1 ticks (150+250)");
        } else if (tk.items[i].pid == 2 && strcmp(tk.items[i].comm, "quickshell") == 0) {
            found_quickshell = true;
            expect(tk.items[i].ticks == 1300, "pid 2 ticks (500+800)");
        }
    }
    expect(found_systemd, "found systemd in ticks");
    expect(found_quickshell, "found quickshell in ticks");
    tam_meter_free_ticks(&tk);

    tam_str_t disp = NULL;
    expect(tam_meter_read_displays(&s, &disp) == 0, "read displays");
    expect(disp != NULL, "displays not null");
    expect(strstr(disp, "DP-1 on") != NULL, "DP-1 on");
    expect(strstr(disp, "DP-2 on") != NULL, "DP-2 on");
    expect(strstr(disp, "HDMI-A-1 off") != NULL, "HDMI-A-1 off");
    tam_str_free(disp);

    double avail_gib = 0.0, swap_gib = 0.0;
    expect(tam_meter_read_meminfo(&s, &avail_gib, &swap_gib) == 0, "read meminfo");
    expect(avail_gib > 41.0 && avail_gib < 42.0, "avail mem roughly 41.2 GiB");
    expect(swap_gib < 0.001, "swap used 0.0 GiB");

    char boot_id[32];
    expect(tam_meter_read_boot_id(&s, boot_id, sizeof(boot_id)) == 0, "read boot id");
    expect(strcmp(boot_id, "da1124be") == 0, "boot id 8 chars matches fixture");

    /* Test stats calculations */
    double samples_odd[] = { 3.0, 5.0, 1.0, 9.0, 2.0 };
    tam_meter_stats_t stat_odd;
    expect(tam_meter_calc_stats(samples_odd, 5, &stat_odd) == 0, "calc stats odd");
    expect(stat_odd.min == 1.0, "odd min");
    expect(stat_odd.max == 9.0, "odd max");
    expect(stat_odd.mean == 4.0, "odd mean");
    expect(stat_odd.median == 3.0, "odd median");

    double samples_even[] = { 1.0, 2.0, 4.0, 5.0 };
    tam_meter_stats_t stat_even;
    expect(tam_meter_calc_stats(samples_even, 4, &stat_even) == 0, "calc stats even");
    expect(stat_even.median == 3.0, "even median (2.0+4.0)/2");

    /* Test report formatting */
    tam_meter_report_data_t rep;
    memset(&rep, 0, sizeof(rep));
    strcpy(rep.when_str, "2026-11-06 17:00 EST");
    rep.settle_seconds = 360;
    rep.minutes = 10.0;
    strcpy(rep.boot_id, "da1124be");
    strcpy(rep.tamlinux_version, "0.6.15");
    strcpy(rep.kernel_release, "7.2.11-arch1-1.1");
    rep.tool_cpu_seconds = 0.04;

    rep.has_power = true;
    rep.power_stats = stat_odd;
    rep.has_temp = true;
    rep.temp_stats = stat_even;

    rep.interrupts_per_sec = 1870.0;
    rep.context_switches_per_sec = 3410.0;
    rep.cpu_busy_percent = 0.9;

    rep.top_proc_count = 2;
    strcpy(rep.top_procs[0].name, "quickshell");
    rep.top_procs[0].cpu_seconds = 3.1;
    strcpy(rep.top_procs[1].name, "Hyprland");
    rep.top_procs[1].cpu_seconds = 2.4;

    strcpy(rep.displays_start, "DP-1 on");
    strcpy(rep.displays_end, "DP-1 off");
    rep.avail_gib = 41.2;
    rep.swap_used_gib = 0.0;
    rep.rapl_readable = false;

    tam_str_t md = NULL;
    tam_meter_format_markdown(&rep, &md);
    expect(strstr(md, "### Energy reading (D170)") != NULL, "md header");
    expect(strstr(md, "tam-meter " TAM_METER_VERSION) != NULL, "md tool");
    expect(strstr(md, "APU power (amdgpu PPT):** mean 4.0 W, median 3.0 W") != NULL, "md power stats");
    expect(strstr(md, "quickshell 3.1 s, Hyprland 2.4 s.") != NULL, "md top procs");
    expect(strstr(md, "RAPL package energy (root-only)") != NULL, "md rapl");
    tam_str_free(md);

    tam_str_t j = NULL;
    tam_meter_format_json(&rep, &j);
    expect(strstr(j, "\"schema\": 1") != NULL, "json schema");
    expect(strstr(j, "\"mean_w\": 4.00") != NULL, "json mean");
    expect(strstr(j, "\"name\": \"quickshell\"") != NULL, "json proc name");
    tam_str_free(j);

    if (g_failures == 0) {
        printf("test_meter: all unit tests passed.\n");
        return 0;
    } else {
        fprintf(stderr, "test_meter: %d test(s) failed.\n", g_failures);
        return 1;
    }
}
