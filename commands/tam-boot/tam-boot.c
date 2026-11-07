#define _POSIX_C_SOURCE 200809L

#include "journal.h"
#include "report.h"
#include "version.h"

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void print_usage(FILE *f)
{
    fprintf(f,
        "Usage: tam-boot [options] [boot_number_or_id]\n"
        "       tam-boot list [options]\n\n"
        "Options:\n"
        "  --json          Output structured JSON\n"
        "  --top K         Show up to K slowest steps (default: 5)\n"
        "  -v, --version   Show version\n"
        "  -h, --help      Show this help\n\n"
        "Examples:\n"
        "  tam-boot            # Explain current boot (boot 0)\n"
        "  tam-boot -1         # Explain previous boot\n"
        "  tam-boot list       # List available boots in the journal\n");
}

int main(int argc, char **argv)
{
    if (argc >= 2) {
        if (strcmp(argv[1], "--version") == 0 || strcmp(argv[1], "-v") == 0) {
            printf("%s\n", TAM_BOOT_VERSION);
            return 0;
        }
        if (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
            print_usage(stdout);
            return 0;
        }
    }

    bool is_list = false;
    bool json = false;
    int top_k = 5;
    int boot_index = 0;
    const char *boot_id = NULL;

    int arg_start = 1;
    if (argc >= 2 && strcmp(argv[1], "list") == 0) {
        is_list = true;
        arg_start = 2;
    }

    static struct option long_opts[] = {
        {"json", no_argument, 0, 'j'},
        {"top", required_argument, 0, 't'},
        {"help", no_argument, 0, 'h'},
        {"version", no_argument, 0, 'v'},
        {0, 0, 0, 0}
    };

    optind = arg_start;
    int opt;
    while ((opt = getopt_long(argc, argv, "jt:hv", long_opts, NULL)) != -1) {
        switch (opt) {
            case 'j': json = true; break;
            case 't': top_k = atoi(optarg); break;
            case 'v': printf("%s\n", TAM_BOOT_VERSION); return 0;
            case 'h': print_usage(stdout); return 0;
            default:
                print_usage(stderr);
                return 1;
        }
    }

    if (optind < argc) {
        const char *arg = argv[optind];
        if (strlen(arg) == 32) {
            boot_id = arg;
        } else {
            boot_index = atoi(arg);
        }
    }

    if (is_list) {
        tam_boot_list_t list;
        if (tam_boot_get_list(&list) != 0) {
            fprintf(stderr, "tam-boot: failed to retrieve boots list from journal\n");
            return 2;
        }
        tam_str_t out = NULL;
        if (json) {
            tam_boot_format_list_json(&list, &out);
        } else {
            tam_boot_format_list_human(&list, &out);
        }
        if (out) {
            printf("%s", out);
            tam_str_free(out);
        }
        tam_boot_free_list(&list);
        return 0;
    }

    tam_boot_analysis_t analysis;
    if (tam_boot_analyze(boot_index, boot_id, &analysis) != 0) {
        fprintf(stderr, "tam-boot: failed to analyze boot\n");
        return 2;
    }

    tam_str_t out = NULL;
    if (json) {
        tam_boot_format_json(&analysis, (size_t)top_k, &out);
    } else {
        tam_boot_format_human(&analysis, (size_t)top_k, &out);
    }

    if (out) {
        printf("%s", out);
        tam_str_free(out);
    }

    return 0;
}
