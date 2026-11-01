#ifndef TAM_HARDWARE_PROBE_H
#define TAM_HARDWARE_PROBE_H

#include <stddef.h>

#define TAM_HARDWARE_FEATURE_MAX 256
#define TAM_HARDWARE_STR 128
#define TAM_HARDWARE_UNAVAIL_MAX 32

struct tam_hardware_report {
	char architecture[TAM_HARDWARE_STR];

	int cpu_ok;
	char vendor[TAM_HARDWARE_STR];
	char brand[TAM_HARDWARE_STR];
	char codename[TAM_HARDWARE_STR];
	int family;
	int model;
	int stepping;
	int cores;
	int logical_cpus;
	char features[TAM_HARDWARE_FEATURE_MAX][TAM_HARDWARE_STR];
	size_t feature_count;

	int caches_ok;
	int l1d_kb;
	int l1i_kb;
	int l2_kb;
	int l3_kb;

	int dmi_any;
	char product_name[TAM_HARDWARE_STR];
	char product_family[TAM_HARDWARE_STR];
	char board_name[TAM_HARDWARE_STR];
	char board_vendor[TAM_HARDWARE_STR];
	char bios_vendor[TAM_HARDWARE_STR];
	char bios_version[TAM_HARDWARE_STR];

	char unavailable[TAM_HARDWARE_UNAVAIL_MAX][TAM_HARDWARE_STR];
	size_t unavailable_count;
};

/* Override DMI/sysfs root for tests (no trailing slash). Empty = host. */
const char *tam_hardware_sysfs_root(void);

/* Fill report. Returns 0 on success (partial OK), -1 if architecture unknown. */
int tam_hardware_probe(struct tam_hardware_report *out);

#endif
