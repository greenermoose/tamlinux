#define _POSIX_C_SOURCE 200809L

#include "probe.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>

#include <libcpuid.h>

static void unavailable_add(struct tam_hardware_report *r, const char *key)
{
	size_t i;

	if (!key || !*key || r->unavailable_count >= TAM_HARDWARE_UNAVAIL_MAX)
		return;
	for (i = 0; i < r->unavailable_count; i++) {
		if (strcmp(r->unavailable[i], key) == 0)
			return;
	}
	snprintf(r->unavailable[r->unavailable_count], TAM_HARDWARE_STR, "%s", key);
	r->unavailable_count++;
}

const char *tam_hardware_sysfs_root(void)
{
	const char *p = getenv("TAM_HARDWARE_SYSFS_ROOT");

	return (p && *p) ? p : "";
}

static void trim_inplace(char *s)
{
	char *end;
	char *start = s;

	while (*start && isspace((unsigned char)*start))
		start++;
	if (start != s)
		memmove(s, start, strlen(start) + 1);
	end = s + strlen(s);
	while (end > s && isspace((unsigned char)end[-1]))
		end--;
	*end = '\0';
}

static int read_sysfs_file(const char *path, char *dst, size_t dst_sz)
{
	FILE *f;
	size_t n;

	if (!path || !dst || dst_sz == 0)
		return -1;
	f = fopen(path, "r");
	if (!f)
		return -1;
	if (!fgets(dst, (int)dst_sz, f)) {
		fclose(f);
		dst[0] = '\0';
		return -1;
	}
	fclose(f);
	n = strlen(dst);
	if (n > 0 && dst[n - 1] == '\n')
		dst[n - 1] = '\0';
	trim_inplace(dst);
	return dst[0] ? 0 : -1;
}

static void read_dmi_field(struct tam_hardware_report *r, const char *name,
			   char *dst, size_t dst_sz, const char *unavail_key)
{
	char path[512];
	const char *root = tam_hardware_sysfs_root();

	if (root[0])
		snprintf(path, sizeof(path), "%s/sys/class/dmi/id/%s", root, name);
	else
		snprintf(path, sizeof(path), "/sys/class/dmi/id/%s", name);
	if (read_sysfs_file(path, dst, dst_sz) == 0)
		r->dmi_any = 1;
	else {
		dst[0] = '\0';
		unavailable_add(r, unavail_key);
	}
}

static int feature_cmp(const void *a, const void *b)
{
	return strcmp((const char *)a, (const char *)b);
}

static int load_cpu_fixture(struct tam_hardware_report *r, const char *path)
{
	FILE *f;
	char line[512];

	f = fopen(path, "r");
	if (!f)
		return -1;
	r->cpu_ok = 1;
	r->caches_ok = 0;
	r->family = -1;
	r->model = -1;
	r->stepping = -1;
	r->cores = -1;
	r->logical_cpus = -1;
	r->l1d_kb = r->l1i_kb = r->l2_kb = r->l3_kb = -1;
	while (fgets(line, sizeof(line), f)) {
		char *eq;
		char *key;
		char *val;

		trim_inplace(line);
		if (!line[0] || line[0] == '#')
			continue;
		eq = strchr(line, '=');
		if (!eq)
			continue;
		*eq = '\0';
		key = line;
		val = eq + 1;
		trim_inplace(key);
		trim_inplace(val);
		if (strcmp(key, "vendor") == 0)
			snprintf(r->vendor, sizeof(r->vendor), "%s", val);
		else if (strcmp(key, "brand") == 0)
			snprintf(r->brand, sizeof(r->brand), "%s", val);
		else if (strcmp(key, "codename") == 0)
			snprintf(r->codename, sizeof(r->codename), "%s", val);
		else if (strcmp(key, "family") == 0)
			r->family = atoi(val);
		else if (strcmp(key, "model") == 0)
			r->model = atoi(val);
		else if (strcmp(key, "stepping") == 0)
			r->stepping = atoi(val);
		else if (strcmp(key, "cores") == 0)
			r->cores = atoi(val);
		else if (strcmp(key, "logical_cpus") == 0)
			r->logical_cpus = atoi(val);
		else if (strcmp(key, "l1d_kb") == 0) {
			r->l1d_kb = atoi(val);
			r->caches_ok = 1;
		} else if (strcmp(key, "l1i_kb") == 0) {
			r->l1i_kb = atoi(val);
			r->caches_ok = 1;
		} else if (strcmp(key, "l2_kb") == 0) {
			r->l2_kb = atoi(val);
			r->caches_ok = 1;
		} else if (strcmp(key, "l3_kb") == 0) {
			r->l3_kb = atoi(val);
			r->caches_ok = 1;
		} else if (strcmp(key, "features") == 0) {
			char *tok;
			char *save = NULL;

			for (tok = strtok_r(val, ", \t", &save); tok;
			     tok = strtok_r(NULL, ", \t", &save)) {
				if (r->feature_count >= TAM_HARDWARE_FEATURE_MAX)
					break;
				snprintf(r->features[r->feature_count], TAM_HARDWARE_STR,
					 "%s", tok);
				r->feature_count++;
			}
		}
	}
	fclose(f);
	if (r->feature_count > 1)
		qsort(r->features, r->feature_count, TAM_HARDWARE_STR, feature_cmp);
	return 0;
}

static int probe_cpu_live(struct tam_hardware_report *r)
{
	struct cpu_raw_data_t raw;
	struct cpu_id_t id;
	int feat;

	if (!cpuid_present()) {
		unavailable_add(r, "cpuid");
		return -1;
	}
	if (cpuid_get_raw_data(&raw) < 0 || cpu_identify(&raw, &id) < 0) {
		unavailable_add(r, "cpuid");
		return -1;
	}
	r->cpu_ok = 1;
	snprintf(r->vendor, sizeof(r->vendor), "%s", id.vendor_str);
	snprintf(r->brand, sizeof(r->brand), "%s", id.brand_str);
	snprintf(r->codename, sizeof(r->codename), "%s", id.cpu_codename);
	/* Prefer display ("true") family/model so values match lscpu. */
	r->family = id.x86.ext_family ? id.x86.ext_family : id.x86.family;
	r->model = id.x86.ext_model ? id.x86.ext_model : id.x86.model;
	r->stepping = id.x86.stepping;
	r->cores = id.num_cores;
	r->logical_cpus = id.total_logical_cpus > 0 ? id.total_logical_cpus
						    : id.num_logical_cpus;
	for (feat = 0; feat < NUM_CPU_FEATURES; feat++) {
		const char *name;

		if (!id.flags[feat])
			continue;
		name = cpu_feature_str((cpu_feature_t)feat);
		if (!name || !*name)
			continue;
		if (r->feature_count >= TAM_HARDWARE_FEATURE_MAX)
			break;
		snprintf(r->features[r->feature_count], TAM_HARDWARE_STR, "%s", name);
		/* normalize to lowercase */
		{
			char *p = r->features[r->feature_count];
			for (; *p; p++)
				*p = (char)tolower((unsigned char)*p);
		}
		r->feature_count++;
	}
	if (r->feature_count > 1)
		qsort(r->features, r->feature_count, TAM_HARDWARE_STR, feature_cmp);

	r->l1d_kb = id.l1_data_cache;
	r->l1i_kb = id.l1_instruction_cache;
	r->l2_kb = id.l2_cache;
	r->l3_kb = id.l3_cache;
	if (r->l1d_kb >= 0 || r->l1i_kb >= 0 || r->l2_kb >= 0 || r->l3_kb >= 0)
		r->caches_ok = 1;
	else
		unavailable_add(r, "caches");
	return 0;
}

int tam_hardware_probe(struct tam_hardware_report *out)
{
	struct utsname uts;
	const char *fixture;

	if (!out)
		return -1;
	memset(out, 0, sizeof(*out));
	out->family = out->model = out->stepping = -1;
	out->cores = out->logical_cpus = -1;
	out->l1d_kb = out->l1i_kb = out->l2_kb = out->l3_kb = -1;

	if (uname(&uts) != 0 || !uts.machine[0])
		return -1;
	snprintf(out->architecture, sizeof(out->architecture), "%s", uts.machine);

	fixture = getenv("TAM_HARDWARE_FIXTURE_CPU");
	if (fixture && *fixture) {
		if (load_cpu_fixture(out, fixture) != 0)
			unavailable_add(out, "cpuid");
	} else if (probe_cpu_live(out) != 0) {
		/* already recorded */
	}

	read_dmi_field(out, "product_name", out->product_name, sizeof(out->product_name),
		       "dmi.product_name");
	read_dmi_field(out, "product_family", out->product_family,
		       sizeof(out->product_family), "dmi.product_family");
	read_dmi_field(out, "board_name", out->board_name, sizeof(out->board_name),
		       "dmi.board_name");
	read_dmi_field(out, "board_vendor", out->board_vendor, sizeof(out->board_vendor),
		       "dmi.board_vendor");
	read_dmi_field(out, "bios_vendor", out->bios_vendor, sizeof(out->bios_vendor),
		       "dmi.bios_vendor");
	read_dmi_field(out, "bios_version", out->bios_version, sizeof(out->bios_version),
		       "dmi.bios_version");

	return 0;
}
