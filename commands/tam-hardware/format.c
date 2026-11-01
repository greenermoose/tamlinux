#include "format.h"

#include <stdio.h>
#include <string.h>

#include <tam.h>

void tam_hardware_format_human(FILE *out, const struct tam_hardware_report *r)
{
	fprintf(out, "Architecture: %s\n", r->architecture);
	if (r->cpu_ok) {
		fprintf(out, "CPU:          %s\n", r->brand[0] ? r->brand : "(unknown)");
		if (r->vendor[0])
			fprintf(out, "Vendor:       %s\n", r->vendor);
		if (r->codename[0])
			fprintf(out, "Codename:     %s\n", r->codename);
		if (r->family >= 0)
			fprintf(out, "Family/Model: %d / %d (stepping %d)\n", r->family,
				r->model, r->stepping);
		if (r->cores >= 0 || r->logical_cpus >= 0)
			fprintf(out, "Cores:        %d physical, %d logical\n",
				r->cores >= 0 ? r->cores : 0,
				r->logical_cpus >= 0 ? r->logical_cpus : 0);
		fprintf(out, "Features:     %zu flags", r->feature_count);
		if (r->feature_count > 0) {
			size_t i;
			size_t show = r->feature_count < 8 ? r->feature_count : 8;

			fprintf(out, " (");
			for (i = 0; i < show; i++) {
				if (i)
					fputc(',', out);
				fputs(r->features[i], out);
			}
			if (r->feature_count > show)
				fprintf(out, ",…");
			fputc(')', out);
		}
		fputc('\n', out);
	} else {
		fprintf(out, "CPU:          (unavailable)\n");
	}
	if (r->caches_ok) {
		fprintf(out, "Caches:       L1d=%d KiB L1i=%d KiB L2=%d KiB L3=%d KiB\n",
			r->l1d_kb, r->l1i_kb, r->l2_kb, r->l3_kb);
	}
	if (r->product_name[0] || r->board_name[0]) {
		fprintf(out, "Product:      %s\n",
			r->product_name[0] ? r->product_name : "(unknown)");
		if (r->board_name[0])
			fprintf(out, "Board:        %s%s%s\n", r->board_name,
				r->board_vendor[0] ? " / " : "",
				r->board_vendor[0] ? r->board_vendor : "");
	}
	if (r->bios_version[0] || r->bios_vendor[0])
		fprintf(out, "BIOS:         %s%s%s\n",
			r->bios_vendor[0] ? r->bios_vendor : "",
			r->bios_vendor[0] && r->bios_version[0] ? " " : "",
			r->bios_version[0] ? r->bios_version : "");
}

static void json_null_or_int(tam_str_t *s, const char *key, int value, int first)
{
	*s = tam_str_cat_printf(*s, "%s\"%s\":", first ? "" : ",", key);
	if (value < 0)
		*s = tam_str_cat(*s, "null");
	else
		*s = tam_str_cat_printf(*s, "%d", value);
}

static void json_str_field(tam_str_t *s, const char *key, const char *value, int first)
{
	*s = tam_str_cat_printf(*s, "%s\"%s\":", first ? "" : ",", key);
	if (!value || !*value)
		*s = tam_str_cat(*s, "null");
	else {
		*s = tam_str_cat(*s, "\"");
		*s = tam_str_cat_json(*s, value);
		*s = tam_str_cat(*s, "\"");
	}
}

int tam_hardware_format_json(FILE *out, const struct tam_hardware_report *r)
{
	tam_str_t s = tam_str_new("{");
	size_t i;

	if (!s)
		return -1;
	s = tam_str_cat(s, "\"schema\":1");
	json_str_field(&s, "architecture", r->architecture, 0);

	s = tam_str_cat(s, ",\"cpu\":{");
	if (r->cpu_ok) {
		json_str_field(&s, "vendor", r->vendor, 1);
		json_str_field(&s, "brand", r->brand, 0);
		json_null_or_int(&s, "family", r->family, 0);
		json_null_or_int(&s, "model", r->model, 0);
		json_null_or_int(&s, "stepping", r->stepping, 0);
		json_str_field(&s, "codename", r->codename, 0);
		json_null_or_int(&s, "cores", r->cores, 0);
		json_null_or_int(&s, "logical_cpus", r->logical_cpus, 0);
		s = tam_str_cat(s, ",\"features\":[");
		for (i = 0; i < r->feature_count; i++) {
			if (i)
				s = tam_str_cat(s, ",");
			s = tam_str_cat(s, "\"");
			s = tam_str_cat_json(s, r->features[i]);
			s = tam_str_cat(s, "\"");
		}
		s = tam_str_cat(s, "]");
	} else {
		s = tam_str_cat(s, "\"vendor\":null,\"brand\":null,\"family\":null,"
				   "\"model\":null,\"stepping\":null,\"codename\":null,"
				   "\"cores\":null,\"logical_cpus\":null,\"features\":[]");
	}
	s = tam_str_cat(s, "}");

	s = tam_str_cat(s, ",\"caches\":{");
	json_null_or_int(&s, "l1d_kb", r->caches_ok ? r->l1d_kb : -1, 1);
	json_null_or_int(&s, "l1i_kb", r->caches_ok ? r->l1i_kb : -1, 0);
	json_null_or_int(&s, "l2_kb", r->caches_ok ? r->l2_kb : -1, 0);
	json_null_or_int(&s, "l3_kb", r->caches_ok ? r->l3_kb : -1, 0);
	s = tam_str_cat(s, "}");

	s = tam_str_cat(s, ",\"dmi\":{");
	json_str_field(&s, "product_name", r->product_name, 1);
	json_str_field(&s, "product_family", r->product_family, 0);
	json_str_field(&s, "board_name", r->board_name, 0);
	json_str_field(&s, "board_vendor", r->board_vendor, 0);
	json_str_field(&s, "bios_vendor", r->bios_vendor, 0);
	json_str_field(&s, "bios_version", r->bios_version, 0);
	s = tam_str_cat(s, "}");

	s = tam_str_cat(s, ",\"unavailable\":[");
	for (i = 0; i < r->unavailable_count; i++) {
		if (i)
			s = tam_str_cat(s, ",");
		s = tam_str_cat(s, "\"");
		s = tam_str_cat_json(s, r->unavailable[i]);
		s = tam_str_cat(s, "\"");
	}
	s = tam_str_cat(s, "]}");

	fputs(s, out);
	fputc('\n', out);
	tam_str_free(s);
	return 0;
}
