#include "screen.h"

#include "util.h"

#include <tam.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void default_write(const char *s, void *user)
{
	(void)user;
	fputs(s, stdout);
}

static void default_flush(void *user)
{
	(void)user;
	fflush(stdout);
}

void start_screen_init(start_screen_t *sc,
		       void (*write_fn)(const char *s, void *user),
		       void (*flush_fn)(void *user),
		       void *user)
{
	memset(sc, 0, sizeof(*sc));
	sc->write_fn = write_fn ? write_fn : default_write;
	sc->flush_fn = flush_fn ? flush_fn : default_flush;
	sc->user = user;
}

void start_screen_clear(start_screen_t *sc)
{
	size_t i;

	if (sc->rows) {
		for (i = 0; i < sc->height; i++)
			free(sc->rows[i]);
		free(sc->rows);
	}
	sc->rows = NULL;
	sc->height = 0;
	sc->width = 0;
}

void start_screen_enter(start_screen_t *sc)
{
	/* ?7l disables wraparound so a full-width footer cannot auto-wrap and
	 * hide its last character (e.g. the final 0 in v0.2.0 / v0.3.0). */
	sc->write_fn("\033[?1049h\033[?7l\033[?25l\033[H\033[2J", sc->user);
	sc->flush_fn(sc->user);
	sc->entered = 1;
	start_screen_clear(sc);
}

void start_screen_leave(start_screen_t *sc)
{
	if (sc->entered) {
		sc->write_fn("\033[?25h\033[?7h\033[?1049l", sc->user);
		sc->flush_fn(sc->user);
		sc->entered = 0;
	}
	start_screen_clear(sc);
}

static int use_sync_update(void)
{
	const char *term = getenv("TERM");
	const char *ct = getenv("COLORTERM");

	if (term && (strncmp(term, "foot", 4) == 0 ||
		     strncmp(term, "xterm", 5) == 0 ||
		     strncmp(term, "kitty", 5) == 0))
		return 1;
	if (ct && (strcmp(ct, "truecolor") == 0 || strcmp(ct, "24bit") == 0))
		return 1;
	return 0;
}

static int append_str(char **out, size_t *len, size_t *cap, const char *s)
{
	size_t n = strlen(s);

	if (*len + n + 1 > *cap) {
		size_t nc = *cap ? *cap * 2 : 256;
		char *no;

		while (nc < *len + n + 1)
			nc *= 2;
		no = realloc(*out, nc);
		if (!no)
			return -1;
		*out = no;
		*cap = nc;
	}
	memcpy(*out + *len, s, n);
	*len += n;
	(*out)[*len] = '\0';
	return 0;
}

int start_screen_update(start_screen_t *sc, char **rows, size_t height, int width)
{
	size_t i;
	int full;
	int changed = 0;
	char *out = NULL;
	size_t out_len = 0;
	size_t out_cap = 0;
	char cup[32];

	full = (!sc->rows || sc->width != width || sc->height != height);

	if (use_sync_update() && append_str(&out, &out_len, &out_cap, "\033[?2026h") != 0)
		goto fail;
	for (i = 0; i < height; i++) {
		const char *row;
		size_t vis;

		if (!full && i < sc->height && sc->rows[i] &&
		    strcmp(sc->rows[i], rows[i]) == 0)
			continue;
		changed++;
		row = rows[i] ? rows[i] : "";
		vis = start_visible_len(row);
		snprintf(cup, sizeof(cup), "\033[%zu;1H", i + 1);
		if (append_str(&out, &out_len, &out_cap, cup) != 0 ||
		    append_str(&out, &out_len, &out_cap, row) != 0)
			goto fail;
		/*
		 * Erase-to-EOL clears from the cursor through the end of the
		 * line, including the current cell. After a full-width write
		 * the cursor sits on the last column, so EL would wipe the
		 * last glyph (the final digit of "v0.2.3"). Only EL when the
		 * row is shorter than the terminal width.
		 */
		if ((int)vis < width) {
			if (append_str(&out, &out_len, &out_cap, "\033[K") != 0)
				goto fail;
		}
		if (append_str(&out, &out_len, &out_cap, "\033[0m") != 0)
			goto fail;
	}
	if (use_sync_update() && append_str(&out, &out_len, &out_cap, "\033[?2026l") != 0)
		goto fail;
	if (changed && out) {
		sc->write_fn(out, sc->user);
		sc->flush_fn(sc->user);
	}
	free(out);

	start_screen_clear(sc);
	sc->rows = calloc(height, sizeof(char *));
	if (!sc->rows)
		return -1;
	sc->height = height;
	sc->width = width;
	for (i = 0; i < height; i++) {
		sc->rows[i] = strdup(rows[i] ? rows[i] : "");
		if (!sc->rows[i])
			return -1;
	}
	return changed;
fail:
	free(out);
	return -1;
}
