#include "menu.h"

#include <tam.h>

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void skip_ws(const char **p)
{
	while (**p && isspace((unsigned char)**p))
		(*p)++;
}

static int expect(const char **p, char c)
{
	skip_ws(p);
	if (**p != c)
		return -1;
	(*p)++;
	return 0;
}

static char *parse_string(const char **p)
{
	tam_str_t out;
	char *plain;
	const char *s;

	skip_ws(p);
	if (**p != '"')
		return NULL;
	(*p)++;
	out = tam_str_new("");
	if (!out)
		return NULL;
	while (**p && **p != '"') {
		if (**p == '\\') {
			(*p)++;
			if (!**p) {
				tam_str_free(out);
				return NULL;
			}
			switch (**p) {
			case '"':
			case '\\':
			case '/':
				out = tam_str_cat_len(out, *p, 1);
				break;
			case 'n':
				out = tam_str_cat(out, "\n");
				break;
			case 't':
				out = tam_str_cat(out, "\t");
				break;
			case 'r':
				out = tam_str_cat(out, "\r");
				break;
			case 'u':
				/* Skip \uXXXX as four hex digits; keep as '?' */
				(*p)++;
				for (int i = 0; i < 4 && isxdigit((unsigned char)**p); i++)
					(*p)++;
				(*p)--;
				out = tam_str_cat(out, "?");
				break;
			default:
				out = tam_str_cat_len(out, *p, 1);
				break;
			}
			(*p)++;
			continue;
		}
		s = *p;
		out = tam_str_cat_len(out, s, 1);
		(*p)++;
	}
	if (**p != '"') {
		tam_str_free(out);
		return NULL;
	}
	(*p)++;
	/* Copy into a plain malloc string; tam_str has a hidden header. */
	plain = strdup(out);
	tam_str_free(out);
	return plain;
}

static int parse_string_array(const char **p, char **argv, int *argc)
{
	int n = 0;

	if (expect(p, '[') != 0)
		return -1;
	skip_ws(p);
	if (**p == ']') {
		(*p)++;
		*argc = 0;
		return 0;
	}
	while (1) {
		char *s;

		if (n >= START_MAX_ARGV)
			return -1;
		s = parse_string(p);
		if (!s)
			return -1;
		argv[n++] = s;
		skip_ws(p);
		if (**p == ',') {
			(*p)++;
			continue;
		}
		if (**p == ']') {
			(*p)++;
			*argc = n;
			return 0;
		}
		return -1;
	}
}

static void activity_clear(start_activity_t *a)
{
	int i;

	free(a->id);
	free(a->category);
	free(a->label);
	free(a->check);
	free(a->description);
	for (i = 0; i < a->argc; i++)
		free(a->argv[i]);
	memset(a, 0, sizeof(*a));
}

static int parse_activity(const char **p, start_activity_t *a)
{
	memset(a, 0, sizeof(*a));
	if (expect(p, '{') != 0)
		return -1;
	skip_ws(p);
	if (**p == '}') {
		(*p)++;
		return -1;
	}
	while (1) {
		char *key;
		char *val;

		key = parse_string(p);
		if (!key)
			goto fail;
		if (expect(p, ':') != 0) {
			free(key);
			goto fail;
		}
		if (strcmp(key, "argv") == 0) {
			free(key);
			if (parse_string_array(p, a->argv, &a->argc) != 0)
				goto fail;
		} else {
			val = parse_string(p);
			if (!val) {
				free(key);
				goto fail;
			}
			if (strcmp(key, "id") == 0)
				a->id = val;
			else if (strcmp(key, "category") == 0)
				a->category = val;
			else if (strcmp(key, "label") == 0)
				a->label = val;
			else if (strcmp(key, "check") == 0)
				a->check = val;
			else if (strcmp(key, "description") == 0)
				a->description = val;
			else
				free(val);
			free(key);
		}
		skip_ws(p);
		if (**p == ',') {
			(*p)++;
			continue;
		}
		if (**p == '}') {
			(*p)++;
			break;
		}
		goto fail;
	}
	if (!a->id || !a->category || !a->label || !a->check || !a->description ||
	    a->argc < 1)
		goto fail;
	return 0;
fail:
	activity_clear(a);
	return -1;
}

int start_menu_load_string(start_menu_t *menu, const char *json)
{
	const char *p = json;
	start_activity_t *items = NULL;
	size_t count = 0;
	size_t cap = 0;

	memset(menu, 0, sizeof(*menu));
	if (expect(&p, '[') != 0)
		return -1;
	skip_ws(&p);
	if (*p == ']') {
		p++;
		return -1; /* empty menu refused */
	}
	while (1) {
		start_activity_t act;

		if (parse_activity(&p, &act) != 0)
			goto fail;
		if (count >= START_MAX_ACTIVITIES) {
			activity_clear(&act);
			goto fail;
		}
		if (count == cap) {
			size_t ncap = cap ? cap * 2 : 8;
			start_activity_t *ni =
				realloc(items, ncap * sizeof(*items));
			if (!ni) {
				activity_clear(&act);
				goto fail;
			}
			items = ni;
			cap = ncap;
		}
		act.letter = (char)('a' + (int)count);
		items[count++] = act;
		skip_ws(&p);
		if (*p == ',') {
			p++;
			continue;
		}
		if (*p == ']') {
			p++;
			break;
		}
		goto fail;
	}
	menu->items = items;
	menu->count = count;
	start_menu_build_rows(menu);
	return 0;
fail:
	for (size_t i = 0; i < count; i++)
		activity_clear(&items[i]);
	free(items);
	memset(menu, 0, sizeof(*menu));
	return -1;
}

int start_menu_load_file(start_menu_t *menu, const char *path)
{
	char *data;
	size_t len;
	int rc;

	data = tam_fs_read_file(path, &len);
	if (!data)
		return -1;
	rc = start_menu_load_string(menu, data);
	free(data);
	return rc;
}

void start_menu_free(start_menu_t *menu)
{
	size_t i;

	if (!menu)
		return;
	for (i = 0; i < menu->count; i++)
		activity_clear(&menu->items[i]);
	free(menu->items);
	free(menu->rows);
	memset(menu, 0, sizeof(*menu));
}

void start_menu_build_rows(start_menu_t *menu)
{
	size_t i;
	size_t n = 0;
	const char *cur = NULL;
	start_row_t *rows;

	free(menu->rows);
	menu->rows = NULL;
	menu->row_count = 0;
	/* worst case: header + choice per item */
	rows = calloc(menu->count * 2, sizeof(*rows));
	if (!rows)
		return;
	for (i = 0; i < menu->count; i++) {
		if (!cur || strcmp(cur, menu->items[i].category) != 0) {
			cur = menu->items[i].category;
			rows[n].kind = START_ROW_HEADER;
			rows[n].text = cur;
			n++;
		}
		rows[n].kind = START_ROW_CHOICE;
		rows[n].index = (int)i;
		rows[n].letter = menu->items[i].letter;
		rows[n].item = &menu->items[i];
		n++;
	}
	menu->rows = rows;
	menu->row_count = n;
}

size_t start_menu_paginate(const start_row_t *rows, size_t row_count,
			   int capacity, size_t *page_starts, size_t *page_lens)
{
	size_t pages = 0;
	size_t i = 0;

	if (capacity < 1)
		capacity = 1;
	if (row_count == 0) {
		page_starts[0] = 0;
		page_lens[0] = 0;
		return 1;
	}
	while (i < row_count) {
		size_t start = i;
		size_t len = 0;

		while (i < row_count) {
			if ((int)len >= capacity)
				break;
			if (rows[i].kind == START_ROW_HEADER &&
			    (int)len + 2 > capacity && len > 0)
				break;
			i++;
			len++;
		}
		page_starts[pages] = start;
		page_lens[pages] = len;
		pages++;
	}
	return pages;
}

size_t start_choice_indices_on_page(const start_row_t *rows, size_t start,
				    size_t len, int *out_indices, size_t out_cap)
{
	size_t n = 0;
	size_t i;

	for (i = 0; i < len; i++) {
		if (rows[start + i].kind != START_ROW_CHOICE)
			continue;
		if (n < out_cap)
			out_indices[n] = rows[start + i].index;
		n++;
	}
	return n;
}

const start_activity_t *start_menu_by_letter(const start_menu_t *menu, char letter)
{
	size_t i;

	for (i = 0; i < menu->count; i++) {
		if (menu->items[i].letter == letter)
			return &menu->items[i];
	}
	return NULL;
}
