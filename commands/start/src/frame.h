#ifndef START_FRAME_H
#define START_FRAME_H

#include "menu.h"

#include <stddef.h>

/* Compose exactly `height` lines into lines[] (caller frees each with free).
 * lines must hold at least height pointers. */
void start_compose_frame(char **lines, size_t height, int width,
			 const start_row_t *page, size_t page_len,
			 int attention_index);

void start_format_footer(char *dst, size_t dstsz, int width);

#endif /* START_FRAME_H */
