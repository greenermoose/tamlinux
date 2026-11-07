#ifndef JOURNAL_H
#define JOURNAL_H

#include <stdbool.h>
#include <stddef.h>
#include <tam.h>

typedef struct {
    char boot_id[33];
    char date_str[64];
    int index;
} tam_boot_entry_t;

typedef struct {
    tam_boot_entry_t *entries;
    size_t count;
} tam_boot_list_t;

typedef struct {
    double timestamp_s;
    double duration_s;
    char desc[128];
} tam_boot_step_t;

typedef struct {
    char boot_id[33];
    char kernel_release[64];
    char date_str[64];

    double firmware_s;
    double loader_s;
    double kernel_s;
    double initrd_s;
    double userspace_s;
    double total_s;

    double kernel_machine_s;
    double passphrase_wait_s;
    bool has_passphrase_wait;

    double getty_ready_s;
    double signin_s;
    double login_wait_s;
    bool has_login;

    double user_session_s;
    bool has_user_session;

    double desktop_ready_s;
    bool has_desktop;

    tam_boot_step_t slow_steps[32];
    size_t slow_step_count;
} tam_boot_analysis_t;

int  tam_boot_get_list(tam_boot_list_t *out);
void tam_boot_free_list(tam_boot_list_t *list);
int  tam_boot_analyze(int boot_index, const char *boot_id_opt, tam_boot_analysis_t *out);

#endif
