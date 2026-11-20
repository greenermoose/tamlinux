#ifndef START_MENU_H
#define START_MENU_H

#include "util.h"

#include <stddef.h>
#include <stdbool.h>

typedef struct {
	char *id;
	char *category;
	char *label;
	char *check;
	char *description;
	char *argv[START_MAX_ARGV];
	int argc;
	char letter;
} start_activity_t;

typedef enum {
	START_ROW_HEADER = 0,
	START_ROW_CHOICE = 1
} start_row_kind_t;

typedef struct {
	start_row_kind_t kind;
	const char *text; /* header */
	int index; /* choice index into activities */
	char letter;
	const start_activity_t *item;
} start_row_t;

typedef struct {
	start_activity_t *items;
	size_t count;
	start_row_t *rows;
	size_t row_count;
} start_menu_t;

int start_menu_load_file(start_menu_t *menu, const char *path);
int start_menu_load_string(start_menu_t *menu, const char *json);
void start_menu_free(start_menu_t *menu);
void start_menu_build_rows(start_menu_t *menu);

/* Paginate into caller-owned pages array of row pointers.
 * Returns number of pages; writes page_starts[i] = first row index of page i
 * and page_lens[i] = row count. Arrays must hold at least row_count slots. */
size_t start_menu_paginate(const start_row_t *rows, size_t row_count,
			   int capacity, size_t *page_starts, size_t *page_lens);

size_t start_choice_indices_on_page(const start_row_t *rows, size_t start,
				    size_t len, int *out_indices, size_t out_cap);

const start_activity_t *start_menu_by_letter(const start_menu_t *menu, char letter);

#endif /* START_MENU_H */
