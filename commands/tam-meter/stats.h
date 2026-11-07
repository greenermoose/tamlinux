#ifndef STATS_H
#define STATS_H

#include <stddef.h>

typedef struct {
    double min;
    double max;
    double mean;
    double median;
    size_t count;
} tam_meter_stats_t;

int tam_meter_calc_stats(const double *samples, size_t count, tam_meter_stats_t *out);

#endif
