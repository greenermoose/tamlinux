#define _POSIX_C_SOURCE 200809L

#include "journal.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void safe_strcpy(char *dest, const char *src, size_t dest_size)
{
    if (!dest || dest_size == 0) return;
    if (!src) { dest[0] = '\0'; return; }
    size_t len = strlen(src);
    if (len >= dest_size) len = dest_size - 1;
    memcpy(dest, src, len);
    dest[len] = '\0';
}

int tam_boot_get_list(tam_boot_list_t *out)
{
    if (!out) return -1;
    out->entries = NULL;
    out->count = 0;

    char *data = NULL;
    size_t len = 0;

    const char *list_file = getenv("TAM_BOOT_LIST_FILE");
    if (list_file) {
        data = tam_fs_read_file(list_file, &len);
    } else {
        const char *const argv[] = { "journalctl", "--list-boots", "--no-pager", NULL };
        tam_exec_result_t res = tam_exec(argv, 5000);
        if (res.exit_code == 0 && res.stdout_buf) {
            data = strdup(res.stdout_buf);
        }
        tam_exec_result_free(&res);
    }

    if (!data) return -1;

    size_t cap = 16;
    out->entries = malloc(cap * sizeof(tam_boot_entry_t));
    if (!out->entries) {
        free(data);
        return -1;
    }

    char *saveptr = NULL;
    char *line = strtok_r(data, "\r\n", &saveptr);
    while (line) {
        while (*line == ' ' || *line == '\t') line++;
        if (*line && *line != 'I') { /* skip header 'IDX ...' */
            int idx = 0;
            char id[64];
            char date[64];
            if (sscanf(line, "%d %63s %63[^\n]", &idx, id, date) >= 2) {
                if (out->count >= cap) {
                    cap *= 2;
                    tam_boot_entry_t *new_e = realloc(out->entries, cap * sizeof(tam_boot_entry_t));
                    if (!new_e) break;
                    out->entries = new_e;
                }
                out->entries[out->count].index = idx;
                safe_strcpy(out->entries[out->count].boot_id, id, sizeof(out->entries[out->count].boot_id));
                safe_strcpy(out->entries[out->count].date_str, date, sizeof(out->entries[out->count].date_str));
                out->count++;
            }
        }
        line = strtok_r(NULL, "\r\n", &saveptr);
    }

    free(data);
    return 0;
}

void tam_boot_free_list(tam_boot_list_t *list)
{
    if (list && list->entries) {
        free(list->entries);
        list->entries = NULL;
        list->count = 0;
    }
}

static void parse_startup_finished_message(const char *msg, tam_boot_analysis_t *out)
{
    /* Format: Startup finished in 9.979s (firmware) + 1.952s (loader) + 13.625s (kernel) + 5.192s (userspace) = 30.749s. */
    const char *p = strstr(msg, "Startup finished in");
    if (!p) return;
    p += 19;

    while (*p && *p != '=') {
        while (*p == ' ' || *p == '+') p++;
        double val = 0.0;
        char part[32] = {0};
        if (sscanf(p, "%lfs (%31[^)])", &val, part) == 2) {
            if (strcmp(part, "firmware") == 0) out->firmware_s = val;
            else if (strcmp(part, "loader") == 0) out->loader_s = val;
            else if (strcmp(part, "kernel") == 0) out->kernel_s = val;
            else if (strcmp(part, "initrd") == 0) out->initrd_s = val;
            else if (strcmp(part, "userspace") == 0) out->userspace_s = val;
        }
        const char *next = strchr(p, '+');
        const char *eq = strchr(p, '=');
        if (next && (!eq || next < eq)) {
            p = next + 1;
        } else if (eq) {
            p = eq;
            break;
        } else {
            break;
        }
    }

    if (*p == '=') {
        p++;
        double tot = 0.0;
        if (sscanf(p, "%lfs", &tot) == 1) {
            out->total_s = tot;
        }
    }
}

static void parse_journal_export_stream(const char *data, size_t len, tam_boot_analysis_t *out)
{
    (void)len;
    const char *p = data;

    unsigned long long enc_start_us = 0;
    unsigned long long enc_end_us = 0;

    unsigned long long prev_kernel_us = 0;
    char prev_kernel_msg[128] = {0};

    while (*p) {
        /* Read one block until empty line or EOF */
        const char *block_start = p;
        const char *block_end = strstr(block_start, "\n\n");
        if (!block_end) {
            block_end = block_start + strlen(block_start);
            p = block_end;
        } else {
            p = block_end + 2;
        }

        /* Scan lines in this record */
        const char *lp = block_start;
        char msg_id[64] = {0};
        char unit[128] = {0};
        char user_unit[128] = {0};
        char message[512] = {0};
        unsigned long long mono_ts = 0;
        unsigned long long src_mono_ts = 0;
        bool is_kernel = false;
        char boot_id[64] = {0};

        while (lp < block_end) {
            const char *eol = memchr(lp, '\n', (size_t)(block_end - lp));
            if (!eol) eol = block_end;
            size_t line_len = (size_t)(eol - lp);

            if (strncmp(lp, "MESSAGE_ID=", 11) == 0) {
                size_t l = line_len - 11;
                if (l >= sizeof(msg_id)) l = sizeof(msg_id) - 1;
                memcpy(msg_id, lp + 11, l);
                msg_id[l] = '\0';
            } else if (strncmp(lp, "MESSAGE=", 8) == 0) {
                size_t l = line_len - 8;
                if (l >= sizeof(message)) l = sizeof(message) - 1;
                memcpy(message, lp + 8, l);
                message[l] = '\0';
            } else if (strncmp(lp, "UNIT=", 5) == 0) {
                size_t l = line_len - 5;
                if (l >= sizeof(unit)) l = sizeof(unit) - 1;
                memcpy(unit, lp + 5, l);
                unit[l] = '\0';
            } else if (strncmp(lp, "USER_UNIT=", 10) == 0) {
                size_t l = line_len - 10;
                if (l >= sizeof(user_unit)) l = sizeof(user_unit) - 1;
                memcpy(user_unit, lp + 10, l);
                user_unit[l] = '\0';
            } else if (strncmp(lp, "__MONOTONIC_TIMESTAMP=", 22) == 0) {
                mono_ts = strtoull(lp + 22, NULL, 10);
            } else if (strncmp(lp, "_SOURCE_MONOTONIC_TIMESTAMP=", 28) == 0) {
                src_mono_ts = strtoull(lp + 28, NULL, 10);
            } else if (strncmp(lp, "_TRANSPORT=kernel", 17) == 0) {
                is_kernel = true;
            } else if (strncmp(lp, "_BOOT_ID=", 9) == 0) {
                size_t l = line_len - 9;
                if (l >= sizeof(boot_id)) l = sizeof(boot_id) - 1;
                memcpy(boot_id, lp + 9, l);
                boot_id[l] = '\0';
            }

            lp = (eol < block_end) ? eol + 1 : block_end;
        }

        bool is_k = is_kernel || (src_mono_ts > 0) || (message[0] == 'L' && strncmp(message, "Linux version ", 14) == 0);

        if (boot_id[0] && !out->boot_id[0]) {
            safe_strcpy(out->boot_id, boot_id, sizeof(out->boot_id));
        }

        /* Check Startup Finished */
        if (strcmp(msg_id, "b07a249cd024414a82dd00cd181378ff") == 0 ||
            strstr(message, "Startup finished in") != NULL) {
            parse_startup_finished_message(message, out);
        }

        /* Check Linux version */
        if (is_k && strncmp(message, "Linux version ", 14) == 0) {
            char ver[64];
            if (sscanf(message + 14, "%63s", ver) == 1) {
                safe_strcpy(out->kernel_release, ver, sizeof(out->kernel_release));
            }
        }

        /* Check Kernel timestamps */
        if (is_k && src_mono_ts > 0) {
            if (strstr(message, "Key type encrypted registered") != NULL) {
                enc_start_us = src_mono_ts;
            } else if (enc_start_us > 0 && enc_end_us == 0) {
                if (strstr(message, "PM: Image not found") != NULL ||
                    strstr(message, "BTRFS") != NULL ||
                    strstr(message, "mapped to") != NULL) {
                    enc_end_us = src_mono_ts;
                }
            }

            if (prev_kernel_us > 0 && src_mono_ts > prev_kernel_us) {
                unsigned long long gap = src_mono_ts - prev_kernel_us;
                /* If gap is > 0.3s and not the passphrase wait */
                if (gap >= 300000) {
                    bool is_enc_gap = (enc_start_us == prev_kernel_us);
                    if (!is_enc_gap && out->slow_step_count < 32) {
                        out->slow_steps[out->slow_step_count].timestamp_s = (double)src_mono_ts / 1e6;
                        out->slow_steps[out->slow_step_count].duration_s = (double)gap / 1e6;
                        snprintf(out->slow_steps[out->slow_step_count].desc,
                                 sizeof(out->slow_steps[out->slow_step_count].desc),
                                 "kernel: after \"%s\", before \"%s\"",
                                 prev_kernel_msg, message);
                        out->slow_step_count++;
                    }
                }
            }

            prev_kernel_us = src_mono_ts;
            safe_strcpy(prev_kernel_msg, message, sizeof(prev_kernel_msg));
        }

        /* Check Getty on tty1 */
        if (strcmp(unit, "getty@tty1.service") == 0 && strstr(message, "Started Getty") != NULL) {
            out->getty_ready_s = (double)mono_ts / 1e6;
        }

        /* Check Logind Sign-in */
        if (!out->has_login && (strcmp(msg_id, "8d45620c1a4348dbb17410da57c60c66") == 0 ||
            strstr(message, "New session") != NULL)) {
            out->signin_s = (double)mono_ts / 1e6;
            out->has_login = true;
        }

        /* Check User Session ready */
        if (strcmp(user_unit, "default.target") == 0 && strstr(message, "Reached target") != NULL) {
            out->user_session_s = (double)mono_ts / 1e6;
            out->has_user_session = true;
        }

        /* Check Graphical Session */
        if (strcmp(user_unit, "graphical-session.target") == 0 && strstr(message, "Reached target") != NULL) {
            out->desktop_ready_s = (double)mono_ts / 1e6;
            out->has_desktop = true;
        }
    }

    if (enc_start_us > 0 && enc_end_us > enc_start_us) {
        out->passphrase_wait_s = (double)(enc_end_us - enc_start_us) / 1e6;
        out->has_passphrase_wait = true;
        if (out->kernel_s >= out->passphrase_wait_s) {
            out->kernel_machine_s = out->kernel_s - out->passphrase_wait_s;
        } else {
            out->kernel_machine_s = out->kernel_s;
        }
    } else {
        out->kernel_machine_s = out->kernel_s;
    }

    if (out->has_login && out->getty_ready_s > 0.0 && out->signin_s >= out->getty_ready_s) {
        out->login_wait_s = out->signin_s - out->getty_ready_s;
    }
}

int tam_boot_analyze(int boot_index, const char *boot_id_opt, tam_boot_analysis_t *out)
{
    if (!out) return -1;
    memset(out, 0, sizeof(*out));

    const char *fix_file = getenv("TAM_BOOT_JOURNAL_FILE");
    if (fix_file) {
        size_t len = 0;
        char *data = tam_fs_read_file(fix_file, &len);
        if (!data) return -1;
        parse_journal_export_stream(data, len, out);
        free(data);
        return 0;
    }

    char boot_arg[32];
    if (boot_id_opt && boot_id_opt[0]) {
        snprintf(boot_arg, sizeof(boot_arg), "%s", boot_id_opt);
    } else {
        snprintf(boot_arg, sizeof(boot_arg), "%d", boot_index);
    }

    /* Run targeted journal queries */
    tam_str_t combined = tam_str_new("");

    /* 1. Startup summary */
    {
        const char *const argv[] = {
            "journalctl", "-b", boot_arg, "MESSAGE_ID=b07a249cd024414a82dd00cd181378ff", "-o", "export", "--no-pager", NULL
        };
        tam_exec_result_t res = tam_exec(argv, 4000);
        if (res.exit_code == 0 && res.stdout_buf) {
            combined = tam_str_cat(combined, res.stdout_buf);
            combined = tam_str_cat(combined, "\n\n");
        }
        tam_exec_result_free(&res);
    }

    /* 2. Getty ready */
    {
        const char *const argv[] = {
            "journalctl", "-b", boot_arg, "-u", "getty@tty1.service", "-o", "export", "--no-pager", NULL
        };
        tam_exec_result_t res = tam_exec(argv, 4000);
        if (res.exit_code == 0 && res.stdout_buf) {
            combined = tam_str_cat(combined, res.stdout_buf);
            combined = tam_str_cat(combined, "\n\n");
        }
        tam_exec_result_free(&res);
    }

    /* 3. Logind sign-in */
    {
        const char *const argv[] = {
            "journalctl", "-b", boot_arg, "MESSAGE_ID=8d45620c1a4348dbb17410da57c60c66", "-o", "export", "--no-pager", NULL
        };
        tam_exec_result_t res = tam_exec(argv, 4000);
        if (res.exit_code == 0 && res.stdout_buf) {
            combined = tam_str_cat(combined, res.stdout_buf);
            combined = tam_str_cat(combined, "\n\n");
        }
        tam_exec_result_free(&res);
    }

    /* 4. User session target */
    {
        const char *const argv[] = {
            "journalctl", "-b", boot_arg, "_UID=1000", "MESSAGE=Reached target Main User Target.", "-o", "export", "--no-pager", NULL
        };
        tam_exec_result_t res = tam_exec(argv, 4000);
        if (res.exit_code == 0 && res.stdout_buf) {
            combined = tam_str_cat(combined, res.stdout_buf);
            combined = tam_str_cat(combined, "\n\n");
        }
        tam_exec_result_free(&res);
    }

    /* 5. Graphical session target */
    {
        const char *const argv[] = {
            "journalctl", "-b", boot_arg, "_UID=1000", "USER_UNIT=graphical-session.target", "-o", "export", "--no-pager", NULL
        };
        tam_exec_result_t res = tam_exec(argv, 4000);
        if (res.exit_code == 0 && res.stdout_buf) {
            combined = tam_str_cat(combined, res.stdout_buf);
            combined = tam_str_cat(combined, "\n\n");
        }
        tam_exec_result_free(&res);
    }

    /* 6. Kernel messages */
    {
        const char *const argv[] = {
            "journalctl", "-b", boot_arg, "-k", "-o", "export", "--output-fields=_SOURCE_MONOTONIC_TIMESTAMP,MESSAGE", "--no-pager", NULL
        };
        tam_exec_result_t res = tam_exec(argv, 8000);
        if (res.exit_code == 0 && res.stdout_buf) {
            combined = tam_str_cat(combined, res.stdout_buf);
            combined = tam_str_cat(combined, "\n\n");
        }
        tam_exec_result_free(&res);
    }

    parse_journal_export_stream(combined, tam_str_len(combined), out);
    tam_str_free(combined);

    return 0;
}
