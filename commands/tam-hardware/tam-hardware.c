#include "format.h"
#include "probe.h"
#include "version.h"

#include <stdio.h>
#include <string.h>

static void usage(FILE *out)
{
	fputs("Usage: tam-hardware [--json] [--version|-v] [--help]\n"
	      "Report host architecture, CPU/ISA features, caches and DMI identity.\n"
	      "Read-only; no root required. Disks: tam-drive-info. Displays: tam-monitor.\n",
	      out);
}

int main(int argc, char **argv)
{
	struct tam_hardware_report report;
	int want_json = 0;
	int i;

	for (i = 1; i < argc; i++) {
		if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
			usage(stdout);
			return 0;
		}
		if (strcmp(argv[i], "--version") == 0 || strcmp(argv[i], "-v") == 0) {
			puts(TAM_HARDWARE_VERSION);
			return 0;
		}
		if (strcmp(argv[i], "--json") == 0) {
			want_json = 1;
			continue;
		}
		fprintf(stderr, "tam-hardware: unknown option %s\n", argv[i]);
		usage(stderr);
		return 1;
	}

	if (tam_hardware_probe(&report) != 0) {
		fputs("tam-hardware: cannot determine architecture\n", stderr);
		return 2;
	}
	if (want_json) {
		if (tam_hardware_format_json(stdout, &report) != 0) {
			fputs("tam-hardware: json format failed\n", stderr);
			return 2;
		}
	} else {
		tam_hardware_format_human(stdout, &report);
	}
	return 0;
}
