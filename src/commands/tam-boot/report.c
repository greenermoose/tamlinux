#define _POSIX_C_SOURCE 200809L

#include "report.h"
#include "version.h"

#include <stdio.h>
#include <string.h>

void tam_boot_format_human(const tam_boot_analysis_t *d, size_t top_k, tam_str_t *out)
{
    if (!d || !out) return;
    *out = tam_str_new("");

    char short_id[9] = {0};
    if (d->boot_id[0]) {
        size_t l = strlen(d->boot_id);
        if (l > 8) l = 8;
        memcpy(short_id, d->boot_id, l);
    } else {
        strcpy(short_id, "current");
    }

    *out = tam_str_cat_printf(*out, "Boot %s", short_id);
    if (d->date_str[0]) {
        *out = tam_str_cat_printf(*out, "  %s", d->date_str);
    }
    if (d->kernel_release[0]) {
        *out = tam_str_cat_printf(*out, "  kernel %s", d->kernel_release);
    }
    *out = tam_str_cat(*out, "\n\n");

    /* Phase lines */
    if (d->firmware_s > 0.0) {
        *out = tam_str_cat_printf(*out, "  firmware     %6.2f s   machine\n", d->firmware_s);
    }
    if (d->loader_s > 0.0) {
        *out = tam_str_cat_printf(*out, "  loader       %6.2f s   machine\n", d->loader_s);
    }
    if (d->kernel_s > 0.0) {
        if (d->has_passphrase_wait) {
            *out = tam_str_cat_printf(*out,
                "  kernel       %6.2f s   = %.2f s machine + %.2f s waiting for you (disk passphrase)\n",
                d->kernel_s, d->kernel_machine_s, d->passphrase_wait_s);
        } else {
            *out = tam_str_cat_printf(*out, "  kernel       %6.2f s   machine\n", d->kernel_s);
        }
    }
    if (d->userspace_s > 0.0) {
        *out = tam_str_cat_printf(*out, "  userspace    %6.2f s   machine, to multi-user.target\n", d->userspace_s);
    }

    /* Milestones */
    if (d->getty_ready_s > 0.0) {
        *out = tam_str_cat_printf(*out, "  text login   %6.2f s   getty@tty1 ready\n", d->getty_ready_s);
    }
    if (d->has_login) {
        *out = tam_str_cat_printf(*out, "  sign-in      %6.2f s   waiting for you (%.2f s since prompt)\n",
            d->signin_s, d->login_wait_s);
    }
    if (d->has_user_session) {
        *out = tam_str_cat_printf(*out, "  user session %6.2f s   user@1000 default.target ready\n", d->user_session_s);
    }
    if (d->has_desktop) {
        *out = tam_str_cat_printf(*out, "  desktop      %6.2f s   graphical-session.target ready\n", d->desktop_ready_s);
    }

    /* Machine time summary */
    if (d->total_s > 0.0) {
        double machine_to_login = d->total_s - d->passphrase_wait_s;
        *out = tam_str_cat_printf(*out,
            "\n  Machine time to text login: %.1f s  (%.1f s total minus %.1f s waiting)\n",
            machine_to_login, d->total_s, d->passphrase_wait_s);
    }

    /* Slow steps */
    if (d->slow_step_count > 0 && top_k > 0) {
        *out = tam_str_cat(*out, "\n  Slowest steps\n");
        size_t count = (d->slow_step_count < top_k) ? d->slow_step_count : top_k;
        for (size_t i = 0; i < count; i++) {
            *out = tam_str_cat_printf(*out, "    %5.2f s  %s\n",
                d->slow_steps[i].duration_s, d->slow_steps[i].desc);
        }
    }
}

void tam_boot_format_json(const tam_boot_analysis_t *d, size_t top_k, tam_str_t *out)
{
    if (!d || !out) return;
    *out = tam_str_new("{\n");
    *out = tam_str_cat(*out, "  \"schema\": 1,\n");
    *out = tam_str_cat_printf(*out, "  \"tool\": \"tam-boot %s\",\n", TAM_BOOT_VERSION);
    *out = tam_str_cat_printf(*out, "  \"boot_id\": \"%s\",\n", d->boot_id);
    *out = tam_str_cat_printf(*out, "  \"kernel\": \"%s\",\n", d->kernel_release);

    *out = tam_str_cat(*out, "  \"totals\": {\n");
    *out = tam_str_cat_printf(*out, "    \"firmware_s\": %.3f,\n", d->firmware_s);
    *out = tam_str_cat_printf(*out, "    \"loader_s\": %.3f,\n", d->loader_s);
    *out = tam_str_cat_printf(*out, "    \"kernel_s\": %.3f,\n", d->kernel_s);
    *out = tam_str_cat_printf(*out, "    \"initrd_s\": %.3f,\n", d->initrd_s);
    *out = tam_str_cat_printf(*out, "    \"userspace_s\": %.3f,\n", d->userspace_s);
    *out = tam_str_cat_printf(*out, "    \"total_s\": %.3f\n", d->total_s);
    *out = tam_str_cat(*out, "  },\n");

    *out = tam_str_cat(*out, "  \"breakdown\": {\n");
    *out = tam_str_cat_printf(*out, "    \"kernel_machine_s\": %.3f,\n", d->kernel_machine_s);
    *out = tam_str_cat_printf(*out, "    \"passphrase_wait_s\": %.3f,\n", d->passphrase_wait_s);
    *out = tam_str_cat_printf(*out, "    \"has_passphrase_wait\": %s,\n", d->has_passphrase_wait ? "true" : "false");
    *out = tam_str_cat_printf(*out, "    \"machine_time_to_login_s\": %.3f\n", d->total_s - d->passphrase_wait_s);
    *out = tam_str_cat(*out, "  },\n");

    *out = tam_str_cat(*out, "  \"milestones\": {\n");
    *out = tam_str_cat_printf(*out, "    \"getty_ready_s\": %.3f,\n", d->getty_ready_s);
    *out = tam_str_cat_printf(*out, "    \"signin_s\": %.3f,\n", d->signin_s);
    *out = tam_str_cat_printf(*out, "    \"login_wait_s\": %.3f,\n", d->login_wait_s);
    *out = tam_str_cat_printf(*out, "    \"user_session_s\": %.3f,\n", d->user_session_s);
    *out = tam_str_cat_printf(*out, "    \"desktop_ready_s\": %.3f\n", d->desktop_ready_s);
    *out = tam_str_cat(*out, "  },\n");

    *out = tam_str_cat(*out, "  \"slow_steps\": [\n");
    size_t count = (d->slow_step_count < top_k) ? d->slow_step_count : top_k;
    for (size_t i = 0; i < count; i++) {
        *out = tam_str_cat(*out, "    {\n");
        *out = tam_str_cat_printf(*out, "      \"duration_s\": %.3f,\n", d->slow_steps[i].duration_s);
        *out = tam_str_cat(*out, "      \"description\": \"");
        *out = tam_str_cat_json(*out, d->slow_steps[i].desc);
        *out = tam_str_cat(*out, "\"\n");
        *out = tam_str_cat_printf(*out, "    }%s\n", (i + 1 < count) ? "," : "");
    }
    *out = tam_str_cat(*out, "  ]\n");

    *out = tam_str_cat(*out, "}\n");
}

void tam_boot_format_list_human(const tam_boot_list_t *list, tam_str_t *out)
{
    if (!list || !out) return;
    *out = tam_str_new("Boots in journal:\n");
    for (size_t i = 0; i < list->count; i++) {
        *out = tam_str_cat_printf(*out, "  %3d  %-32.32s  %s\n",
            list->entries[i].index,
            list->entries[i].boot_id,
            list->entries[i].date_str);
    }
}

void tam_boot_format_list_json(const tam_boot_list_t *list, tam_str_t *out)
{
    if (!list || !out) return;
    *out = tam_str_new("{\n");
    *out = tam_str_cat(*out, "  \"schema\": 1,\n");
    *out = tam_str_cat_printf(*out, "  \"tool\": \"tam-boot %s\",\n", TAM_BOOT_VERSION);
    *out = tam_str_cat(*out, "  \"boots\": [\n");
    for (size_t i = 0; i < list->count; i++) {
        *out = tam_str_cat_printf(*out,
            "    {\"index\": %d, \"boot_id\": \"%s\", \"date\": \"%s\"}%s\n",
            list->entries[i].index,
            list->entries[i].boot_id,
            list->entries[i].date_str,
            (i + 1 < list->count) ? "," : "");
    }
    *out = tam_str_cat(*out, "  ]\n}\n");
}
