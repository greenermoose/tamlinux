#include "stats.h"

#include <stdlib.h>
#include <string.h>

static int compare_double(const void *a, const void *b)
{
    double da = *(const double *)a;
    double db = *(const double *)b;
    if (da < db) return -1;
    if (da > db) return 1;
    return 0;
}

int tam_meter_calc_stats(const double *samples, size_t count, tam_meter_stats_t *out)
{
    if (!samples || count == 0 || !out) return -1;
    memset(out, 0, sizeof(*out));
    out->count = count;

    double sum = 0.0;
    double min_v = samples[0];
    double max_v = samples[0];

    for (size_t i = 0; i < count; i++) {
        double v = samples[i];
        sum += v;
        if (v < min_v) min_v = v;
        if (v > max_v) max_v = v;
    }

    out->min = min_v;
    out->max = max_v;
    out->mean = sum / (double)count;

    double *sorted = malloc(count * sizeof(double));
    if (!sorted) {
        out->median = out->mean;
        return 0;
    }
    memcpy(sorted, samples, count * sizeof(double));
    qsort(sorted, count, sizeof(double), compare_double);

    if (count % 2 == 1) {
        out->median = sorted[count / 2];
    } else {
        out->median = (sorted[(count / 2) - 1] + sorted[count / 2]) / 2.0;
    }
    free(sorted);

    return 0;
}
