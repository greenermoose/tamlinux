#include "frame.h"

#include "util.h"

#include <tam.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void banner_raw(char *dst, size_t dstsz, int which)
{
	switch (which) {
	case 0:
		snprintf(dst, dstsz, "       /\\");
		break;
	case 1:
		snprintf(dst, dstsz, "      /\\/\\");
		break;
	case 2:
		snprintf(dst, dstsz, "     ///\\\\\\       %sTamlinux Start%s",
			 start_sgr_bold(), start_sgr_reset());
		break;
	default:
		snprintf(dst, dstsz, "       ||");
		break;
	}
}

void start_format_footer(char *dst, size_t dstsz, int width)
{
	char left[256];
	char right[64];
	char line[512];
	size_t lvis;
	size_t rvis;
	int gap;
	size_t keep;

	snprintf(left, sizeof(left), "%s", START_FOOTER_HINTS);
	snprintf(right, sizeof(right), "v%s", start_version());
	lvis = start_visible_len(left);
	rvis = start_visible_len(right);
	if ((int)(lvis + 1 + rvis) > width) {
		keep = (size_t)width > rvis + 1 ? (size_t)width - rvis - 1 : 0;
		if (keep && strlen(START_FOOTER_HINTS) > keep) {
			if (keep > 1) {
				memcpy(left, START_FOOTER_HINTS, keep - 1);
				left[keep - 1] = '\0';
				strcat(left, "…");
			} else {
				left[0] = '\0';
			}
		} else {
			left[keep] = '\0';
		}
		lvis = start_visible_len(left);
	}
	gap = width - (int)lvis - (int)rvis;
	if (gap < 1) {
		gap = 1;
		keep = (size_t)width > rvis + 1 ? (size_t)width - rvis - 1 : 0;
		left[keep] = '\0';
		lvis = start_visible_len(left);
		gap = width - (int)lvis - (int)rvis;
		if (gap < 1)
			gap = 1;
	}
	snprintf(line, sizeof(line), "%s%*s%s", left, gap, "", right);
	if (start_use_color())
		snprintf(dst, dstsz, "%s%s%s", start_sgr_dim(), line, start_sgr_reset());
	else
		snprintf(dst, dstsz, "%s", line);
}

static void format_choice(char *dst, size_t dstsz, const start_row_t *row,
			  int width, int focused)
{
	char body[512];
	char clipped[512];
	int installed;
	const char *status;

	installed = start_command_on_path(row->item->check);
	status = installed ? "" : " [not installed]";
	snprintf(body, sizeof(body), "  [%c] %s%s", row->letter, row->item->label,
		 status);
	start_clip_pad(clipped, sizeof(clipped), body, width);
	if (focused) {
		if (start_use_color()) {
			snprintf(dst, dstsz, "%s%s%s", start_attention_on(), clipped,
				 start_attention_off());
		} else {
			if (clipped[0] == ' ')
				clipped[0] = '>';
			snprintf(dst, dstsz, "%s", clipped);
		}
		return;
	}
	if (!installed && start_use_color()) {
		snprintf(dst, dstsz, "%s%s%s", start_sgr_dim(), clipped,
			 start_sgr_reset());
		return;
	}
	snprintf(dst, dstsz, "%s", clipped);
}

static void format_header(char *dst, size_t dstsz, const start_row_t *row, int width)
{
	char text[512];
	char clipped[512];
	char plain[512];
	size_t pvis;

	snprintf(text, sizeof(text), "  ── %s ──", row->text);
	start_clip_pad(clipped, sizeof(clipped), text, width);
	if (start_use_color()) {
		start_strip_ansi(plain, sizeof(plain), clipped);
		while (strlen(plain) && plain[strlen(plain) - 1] == ' ')
			plain[strlen(plain) - 1] = '\0';
		pvis = start_visible_len(plain);
		snprintf(dst, dstsz, "%s%s%s%s", start_sgr_cyan(), start_sgr_bold(),
			 plain, start_sgr_reset());
		while (pvis < (size_t)width && strlen(dst) + 1 < dstsz) {
			strcat(dst, " ");
			pvis++;
		}
	} else {
		snprintf(dst, dstsz, "%s", clipped);
	}
}

void start_compose_frame(char **lines, size_t height, int width,
			 const start_row_t *page, size_t page_len,
			 int attention_index)
{
	size_t i;
	size_t n = 0;
	char raw[1024];
	char tmp[1024];

	for (i = 0; i < 4 && n < height - 1; i++) {
		banner_raw(raw, sizeof(raw), (int)i);
		start_clip_pad(tmp, sizeof(tmp), raw, width);
		lines[n++] = strdup(tmp);
	}
	if (n < height - 1) {
		memset(tmp, ' ', (size_t)width);
		tmp[width] = '\0';
		lines[n++] = strdup(tmp);
	}
	if (n < height - 1) {
		start_clip_pad(tmp, sizeof(tmp),
			       "Choose what to start with your workstation:", width);
		lines[n++] = strdup(tmp);
	}
	if (n < height - 1) {
		memset(tmp, ' ', (size_t)width);
		tmp[width] = '\0';
		lines[n++] = strdup(tmp);
	}
	for (i = 0; i < page_len && n < height - 1; i++) {
		if (page[i].kind == START_ROW_HEADER)
			format_header(tmp, sizeof(tmp), &page[i], width);
		else
			format_choice(tmp, sizeof(tmp), &page[i], width,
				      page[i].index == attention_index);
		lines[n++] = strdup(tmp);
	}
	while (n < height - 1) {
		memset(tmp, ' ', (size_t)width);
		tmp[width] = '\0';
		lines[n++] = strdup(tmp);
	}
	start_format_footer(tmp, sizeof(tmp), width);
	lines[n++] = strdup(tmp);
	while (n < height)
		lines[n++] = strdup("");
}
