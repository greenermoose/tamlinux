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

	/*
	 * Version is never truncated. Reserve its columns first, then fit
	 * hints into the remainder. Trailing ".0" patch numbers (0.2.0,
	 * 0.3.0, …) must remain intact — a prior full-width write could
	 * auto-wrap and hide the last digit on some terminals; the screen
	 * layer disables wrap, and this layout always keeps `right` whole.
	 */
	snprintf(right, sizeof(right), "v%s", start_version());
	rvis = start_visible_len(right);
	if (width < 1) {
		dst[0] = '\0';
		return;
	}
	if ((int)rvis >= width) {
		/* Pathological narrow terminal: show as much version as fits. */
		snprintf(line, sizeof(line), "%s", right);
		start_clip_pad(dst, dstsz, line, width);
		return;
	}

	snprintf(left, sizeof(left), "%s", START_FOOTER_HINTS);
	lvis = start_visible_len(left);
	/* Need at least one gap column between hints and version when both fit. */
	if ((int)(lvis + 1 + rvis) > width) {
		keep = (size_t)width - rvis;
		if (keep > 0)
			keep--; /* gap */
		if (keep == 0) {
			left[0] = '\0';
		} else if (strlen(START_FOOTER_HINTS) > keep) {
			if (keep >= 4) {
				memcpy(left, START_FOOTER_HINTS, keep - 3);
				left[keep - 3] = '\0';
				strcat(left, "...");
			} else {
				memcpy(left, START_FOOTER_HINTS, keep);
				left[keep] = '\0';
			}
		} else {
			left[keep] = '\0';
		}
		lvis = start_visible_len(left);
	}

	gap = width - (int)lvis - (int)rvis;
	if (gap < 1)
		gap = 1;
	/* Re-trim hints if gap forced the line over width (should not happen). */
	while ((int)lvis + gap + (int)rvis > width && lvis > 0) {
		left[strlen(left) > 0 ? strlen(left) - 1 : 0] = '\0';
		lvis = start_visible_len(left);
		gap = width - (int)lvis - (int)rvis;
		if (gap < 1)
			gap = 1;
	}

	snprintf(line, sizeof(line), "%s%*s%s", left, gap, "", right);
	/* Guarantee the version suffix is present and complete. */
	if (!strstr(line, right)) {
		snprintf(line, sizeof(line), "%*s%s",
			 width > (int)rvis ? width - (int)rvis : 0, "", right);
	}
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
