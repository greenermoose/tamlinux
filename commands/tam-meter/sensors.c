#define _POSIX_C_SOURCE 200809L

#include "sensors.h"

#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>

static void safe_strcpy(char *dest, const char *src, size_t dest_size)
{
    if (!dest || dest_size == 0) return;
    if (!src) { dest[0] = '\0'; return; }
    size_t len = strlen(src);
    if (len >= dest_size) len = dest_size - 1;
    memcpy(dest, src, len);
    dest[len] = '\0';
}

static void trim_trailing(char *s)
{
    size_t l = strlen(s);
    while (l > 0 && (s[l - 1] == '\n' || s[l - 1] == '\r' || s[l - 1] == ' ' || s[l - 1] == '\t')) {
        s[l - 1] = '\0';
        l--;
    }
}

static bool read_single_line(const char *path, char *buf, size_t max_len)
{
    FILE *f = fopen(path, "r");
    if (!f) return false;
    if (!fgets(buf, (int)max_len, f)) {
        fclose(f);
        return false;
    }
    fclose(f);
    trim_trailing(buf);
    return true;
}

int tam_meter_init_sensors(tam_meter_sensors_t *s, const char *sysfs_override, const char *proc_override)
{
    if (!s) return -1;
    memset(s, 0, sizeof(*s));

    const char *sys_env = getenv("TAM_METER_SYSFS_ROOT");
    const char *proc_env = getenv("TAM_METER_PROC_ROOT");

    const char *sys_root = sysfs_override ? sysfs_override : (sys_env ? sys_env : "/sys");
    const char *proc_root = proc_override ? proc_override : (proc_env ? proc_env : "/proc");

    safe_strcpy(s->sysfs_root, sys_root, sizeof(s->sysfs_root));
    safe_strcpy(s->proc_root, proc_root, sizeof(s->proc_root));

    /* Check hwmon devices */
    char *hwmon_dir = tam_path_join(s->sysfs_root, "class/hwmon");
    if (hwmon_dir) {
        DIR *d = opendir(hwmon_dir);
        if (d) {
            struct dirent *ent;
            while ((ent = readdir(d)) != NULL) {
                if (ent->d_name[0] == '.') continue;
                char *dev_dir = tam_path_join(hwmon_dir, ent->d_name);
                if (!dev_dir) continue;

                char *name_path = tam_path_join(dev_dir, "name");
                char name_buf[128];
                if (name_path && read_single_line(name_path, name_buf, sizeof(name_buf))) {
                    if (strcmp(name_buf, "amdgpu") == 0 && !s->power_available) {
                        char *power_path = tam_path_join(dev_dir, "power1_input");
                        if (power_path && access(power_path, R_OK) == 0) {
                            safe_strcpy(s->power_path, power_path, sizeof(s->power_path));
                            s->power_available = true;
                        }
                        if (power_path) free(power_path);
                    } else if (strcmp(name_buf, "k10temp") == 0 && !s->temp_available) {
                        char *temp_path = tam_path_join(dev_dir, "temp1_input");
                        if (temp_path && access(temp_path, R_OK) == 0) {
                            safe_strcpy(s->temp_path, temp_path, sizeof(s->temp_path));
                            s->temp_available = true;
                        }
                        if (temp_path) free(temp_path);
                    }
                }
                if (name_path) free(name_path);
                free(dev_dir);
            }
            closedir(d);
        }
        free(hwmon_dir);
    }

    /* Check RAPL */
    char *rapl_path = tam_path_join(s->sysfs_root, "class/powercap/intel-rapl:0/energy_uj");
    if (rapl_path) {
        s->rapl_readable = (access(rapl_path, R_OK) == 0);
        free(rapl_path);
    }

    return 0;
}

int tam_meter_read_power_w(const tam_meter_sensors_t *s, double *out_w)
{
    if (!s || !s->power_available || !out_w) return -1;
    char buf[64];
    if (!read_single_line(s->power_path, buf, sizeof(buf))) return -1;
    long long uw = atoll(buf);
    *out_w = (double)uw / 1e6;
    return 0;
}

int tam_meter_read_temp_c(const tam_meter_sensors_t *s, double *out_c)
{
    if (!s || !s->temp_available || !out_c) return -1;
    char buf[64];
    if (!read_single_line(s->temp_path, buf, sizeof(buf))) return -1;
    long long mc = atoll(buf);
    *out_c = (double)mc / 1e3;
    return 0;
}

int tam_meter_read_stat(const tam_meter_sensors_t *s, tam_meter_stat_t *out)
{
    if (!s || !out) return -1;
    memset(out, 0, sizeof(*out));

    char *path = tam_path_join(s->proc_root, "stat");
    if (!path) return -1;
    FILE *f = fopen(path, "r");
    free(path);
    if (!f) return -1;

    char line[1024];
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "cpu ", 4) == 0) {
            unsigned long long u, n, sy, id, io, ir, si, st, g, gn;
            int count = sscanf(line + 4, "%llu %llu %llu %llu %llu %llu %llu %llu %llu %llu",
                               &u, &n, &sy, &id, &io, &ir, &si, &st, &g, &gn);
            if (count >= 4) {
                unsigned long long total = u + n + sy + id;
                if (count >= 5) total += io;
                if (count >= 6) total += ir;
                if (count >= 7) total += si;
                if (count >= 8) total += st;
                if (count >= 9) total += g;
                if (count >= 10) total += gn;

                unsigned long long idle_total = id + (count >= 5 ? io : 0);
                out->total = total;
                out->busy = (total > idle_total) ? (total - idle_total) : 0;
            }
        } else if (strncmp(line, "intr ", 5) == 0) {
            sscanf(line + 5, "%llu", &out->intr);
        } else if (strncmp(line, "ctxt ", 5) == 0) {
            sscanf(line + 5, "%llu", &out->ctxt);
        }
    }
    fclose(f);
    return 0;
}

int tam_meter_read_ticks(const tam_meter_sensors_t *s, tam_meter_ticks_t *out)
{
    if (!s || !out) return -1;
    out->items = NULL;
    out->count = 0;
    out->capacity = 0;

    DIR *d = opendir(s->proc_root);
    if (!d) return -1;

    struct dirent *ent;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] < '0' || ent->d_name[0] > '9') continue;
        int pid = atoi(ent->d_name);
        if (pid <= 0) continue;

        char *pid_dir = tam_path_join(s->proc_root, ent->d_name);
        if (!pid_dir) continue;
        char *stat_path = tam_path_join(pid_dir, "stat");
        free(pid_dir);
        if (!stat_path) continue;

        FILE *f = fopen(stat_path, "r");
        free(stat_path);
        if (!f) continue;

        char buf[2048];
        if (!fgets(buf, sizeof(buf), f)) {
            fclose(f);
            continue;
        }
        fclose(f);

        char *open_p = strchr(buf, '(');
        char *close_p = strrchr(buf, ')');
        if (!open_p || !close_p || close_p <= open_p) continue;

        char comm[64];
        size_t comm_len = (size_t)(close_p - open_p - 1);
        if (comm_len >= sizeof(comm)) comm_len = sizeof(comm) - 1;
        memcpy(comm, open_p + 1, comm_len);
        comm[comm_len] = '\0';

        char *rest = close_p + 2;
        char *saveptr = NULL;
        char *tok = strtok_r(rest, " ", &saveptr);
        int idx = 0;
        unsigned long long utime = 0, stime = 0;
        while (tok) {
            if (idx == 11) {
                utime = strtoull(tok, NULL, 10);
            } else if (idx == 12) {
                stime = strtoull(tok, NULL, 10);
                break;
            }
            tok = strtok_r(NULL, " ", &saveptr);
            idx++;
        }

        if (out->count >= out->capacity) {
            size_t new_cap = out->capacity ? out->capacity * 2 : 64;
            tam_meter_proc_tick_t *new_items = realloc(out->items, new_cap * sizeof(tam_meter_proc_tick_t));
            if (!new_items) break;
            out->items = new_items;
            out->capacity = new_cap;
        }

        out->items[out->count].pid = pid;
        safe_strcpy(out->items[out->count].comm, comm, sizeof(out->items[out->count].comm));
        out->items[out->count].ticks = utime + stime;
        out->count++;
    }
    closedir(d);
    return 0;
}

void tam_meter_free_ticks(tam_meter_ticks_t *ticks)
{
    if (ticks && ticks->items) {
        free(ticks->items);
        ticks->items = NULL;
        ticks->count = 0;
        ticks->capacity = 0;
    }
}

int tam_meter_read_displays(const tam_meter_sensors_t *s, tam_str_t *out)
{
    if (!s || !out) return -1;
    *out = tam_str_new("");

    char *drm_dir = tam_path_join(s->sysfs_root, "class/drm");
    if (!drm_dir) return -1;

    DIR *d = opendir(drm_dir);
    if (!d) {
        free(drm_dir);
        return -1;
    }

    struct dirent *ent;
    int found_count = 0;
    while ((ent = readdir(d)) != NULL) {
        if (ent->d_name[0] == '.') continue;
        if (strncmp(ent->d_name, "card", 4) != 0) continue;
        char *dash = strchr(ent->d_name, '-');
        if (!dash) continue;

        const char *conn_name = dash + 1;

        char *dev_dir = tam_path_join(drm_dir, ent->d_name);
        if (!dev_dir) continue;

        char *status_path = tam_path_join(dev_dir, "status");
        char status_buf[64];
        bool is_connected = false;
        if (status_path && read_single_line(status_path, status_buf, sizeof(status_buf))) {
            if (strncmp(status_buf, "connected", 9) == 0) {
                is_connected = true;
            }
        }
        if (status_path) free(status_path);

        if (is_connected) {
            char *dpms_path = tam_path_join(dev_dir, "dpms");
            char dpms_buf[64];
            bool on = false;
            if (dpms_path && read_single_line(dpms_path, dpms_buf, sizeof(dpms_buf))) {
                if (strstr(dpms_buf, "On") != NULL) on = true;
            }
            if (dpms_path) free(dpms_path);

            if (found_count > 0) {
                *out = tam_str_cat(*out, ", ");
            }
            *out = tam_str_cat_printf(*out, "%s %s", conn_name, on ? "on" : "off");
            found_count++;
        }
        free(dev_dir);
    }
    closedir(d);
    free(drm_dir);

    if (found_count == 0) {
        *out = tam_str_cat(*out, "none");
    }
    return 0;
}

int tam_meter_read_meminfo(const tam_meter_sensors_t *s, double *out_avail_gib, double *out_swap_used_gib)
{
    if (!s || !out_avail_gib || !out_swap_used_gib) return -1;
    *out_avail_gib = 0.0;
    *out_swap_used_gib = 0.0;

    char *path = tam_path_join(s->proc_root, "meminfo");
    if (!path) return -1;
    FILE *f = fopen(path, "r");
    free(path);
    if (!f) return -1;

    char line[256];
    unsigned long long avail_kb = 0, swap_total_kb = 0, swap_free_kb = 0;
    while (fgets(line, sizeof(line), f)) {
        if (strncmp(line, "MemAvailable:", 13) == 0) {
            sscanf(line + 13, "%llu", &avail_kb);
        } else if (strncmp(line, "SwapTotal:", 10) == 0) {
            sscanf(line + 10, "%llu", &swap_total_kb);
        } else if (strncmp(line, "SwapFree:", 9) == 0) {
            sscanf(line + 9, "%llu", &swap_free_kb);
        }
    }
    fclose(f);

    *out_avail_gib = (double)avail_kb / 1048576.0;
    unsigned long long swap_used = (swap_total_kb > swap_free_kb) ? (swap_total_kb - swap_free_kb) : 0;
    *out_swap_used_gib = (double)swap_used / 1048576.0;
    return 0;
}

int tam_meter_read_boot_id(const tam_meter_sensors_t *s, char *out_boot_id, size_t max_len)
{
    if (!s || !out_boot_id || max_len == 0) return -1;
    char *path = tam_path_join(s->proc_root, "sys/kernel/random/boot_id");
    if (!path) return -1;

    char buf[128];
    if (read_single_line(path, buf, sizeof(buf))) {
        free(path);
        size_t l = strlen(buf);
        if (l > 8) l = 8;
        if (l >= max_len) l = max_len - 1;
        memcpy(out_boot_id, buf, l);
        out_boot_id[l] = '\0';
        return 0;
    }
    free(path);
    safe_strcpy(out_boot_id, "unknown", max_len);
    return -1;
}

int tam_meter_read_tamlinux_version(char *out_version, size_t max_len)
{
    if (!out_version || max_len == 0) return -1;
    const char *home = getenv("HOME");
    if (home) {
        char *user_path = tam_path_join(home, ".config/tamlinux/version");
        if (user_path) {
            if (read_single_line(user_path, out_version, max_len)) {
                free(user_path);
                return 0;
            }
            free(user_path);
        }
    }
    if (read_single_line("/etc/tamlinux/version", out_version, max_len)) {
        return 0;
    }
    safe_strcpy(out_version, "0.6.15", max_len);
    return 0;
}

double tam_meter_read_self_cpu_seconds(const tam_meter_sensors_t *s)
{
    if (!s) return 0.0;
    char *stat_path = tam_path_join(s->proc_root, "self/stat");
    if (!stat_path) return 0.0;

    FILE *f = fopen(stat_path, "r");
    free(stat_path);
    if (!f) return 0.0;

    char buf[2048];
    if (!fgets(buf, sizeof(buf), f)) {
        fclose(f);
        return 0.0;
    }
    fclose(f);

    char *close_p = strrchr(buf, ')');
    if (!close_p) return 0.0;

    char *rest = close_p + 2;
    char *saveptr = NULL;
    char *tok = strtok_r(rest, " ", &saveptr);
    int idx = 0;
    unsigned long long utime = 0, stime = 0;
    while (tok) {
        if (idx == 11) {
            utime = strtoull(tok, NULL, 10);
        } else if (idx == 12) {
            stime = strtoull(tok, NULL, 10);
            break;
        }
        tok = strtok_r(NULL, " ", &saveptr);
        idx++;
    }

    long hz = sysconf(_SC_CLK_TCK);
    if (hz <= 0) hz = 100;
    return (double)(utime + stime) / (double)hz;
}
