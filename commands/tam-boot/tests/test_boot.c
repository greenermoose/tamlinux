#define _POSIX_C_SOURCE 200809L

#include "journal.h"
#include "report.h"
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
    setenv("TAM_BOOT_LIST_FILE", "tests/fixtures/boots_list.txt", 1);
    setenv("TAM_BOOT_JOURNAL_FILE", "tests/fixtures/journal_export_boot0.txt", 1);

    tam_boot_list_t list;
    expect(tam_boot_get_list(&list) == 0, "get boot list from fixture");
    expect(list.count >= 6, "at least 6 boots in list");
    bool found_boot0 = false;
    for (size_t i = 0; i < list.count; i++) {
        if (list.entries[i].index == 0) {
            found_boot0 = true;
            expect(strcmp(list.entries[i].boot_id, "da1124bec34949f28d123f0baa0e224c") == 0, "boot 0 id");
        }
    }
    expect(found_boot0, "found boot 0 in list");
    tam_boot_free_list(&list);

    tam_boot_analysis_t an;
    expect(tam_boot_analyze(0, NULL, &an) == 0, "analyze boot 0");
    expect(strcmp(an.boot_id, "da1124bec34949f28d123f0baa0e224c") == 0, "boot_id matches");
    expect(strcmp(an.kernel_release, "7.2.11-arch1-1.1") == 0, "kernel release matches");

    expect(fabs(an.firmware_s - 9.979) < 0.01, "firmware seconds");
    expect(fabs(an.loader_s - 1.952) < 0.01, "loader seconds");
    expect(fabs(an.kernel_s - 13.625) < 0.01, "kernel seconds");
    expect(fabs(an.userspace_s - 5.192) < 0.01, "userspace seconds");
    expect(fabs(an.total_s - 30.749) < 0.01, "total seconds");

    expect(an.has_passphrase_wait, "has passphrase wait");
    expect(fabs(an.passphrase_wait_s - 8.155) < 0.05, "passphrase wait ~8.16 s");
    expect(fabs(an.kernel_machine_s - 5.47) < 0.05, "kernel machine time ~5.47 s");

    expect(fabs(an.getty_ready_s - 17.046) < 0.05, "getty ready monotonic ~17.05 s");
    expect(an.has_login, "has login");
    expect(fabs(an.signin_s - 43.734) < 0.05, "sign in monotonic ~43.73 s");
    expect(an.has_user_session, "has user session");
    expect(fabs(an.user_session_s - 43.943) < 0.05, "user session ~43.94 s");

    tam_str_t human = NULL;
    tam_boot_format_human(&an, 5, &human);
    expect(human != NULL, "human report not null");
    expect(strstr(human, "Boot da1124be") != NULL, "report header boot id");
    expect(strstr(human, "waiting for you (disk passphrase)") != NULL, "report passphrase wait line");
    expect(strstr(human, "Machine time to text login: 22.6 s") != NULL, "machine time to text login summary");
    tam_str_free(human);

    tam_str_t j = NULL;
    tam_boot_format_json(&an, 5, &j);
    expect(j != NULL, "json report not null");
    expect(strstr(j, "\"schema\": 1") != NULL, "json schema");
    expect(strstr(j, "\"boot_id\": \"da1124bec34949f28d123f0baa0e224c\"") != NULL, "json boot id");
    expect(strstr(j, "\"passphrase_wait_s\":") != NULL, "json passphrase wait field");
    tam_str_free(j);

    if (g_failures == 0) {
        printf("test_boot: all unit tests passed.\n");
        return 0;
    } else {
        fprintf(stderr, "test_boot: %d test(s) failed.\n", g_failures);
        return 1;
    }
}
