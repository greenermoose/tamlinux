#ifndef TAM_HARDWARE_FORMAT_H
#define TAM_HARDWARE_FORMAT_H

#include "probe.h"

#include <stdio.h>

void tam_hardware_format_human(FILE *out, const struct tam_hardware_report *r);
int tam_hardware_format_json(FILE *out, const struct tam_hardware_report *r);

#endif
