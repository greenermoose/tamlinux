#ifndef REPORT_H
#define REPORT_H

#include "journal.h"
#include <tam.h>

void tam_boot_format_human(const tam_boot_analysis_t *data, size_t top_k, tam_str_t *out);
void tam_boot_format_json(const tam_boot_analysis_t *data, size_t top_k, tam_str_t *out);
void tam_boot_format_list_human(const tam_boot_list_t *list, tam_str_t *out);
void tam_boot_format_list_json(const tam_boot_list_t *list, tam_str_t *out);

#endif
