#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include "util.h"

#include <tam.h>

#include <ctype.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static char g_version[64];
static int g_version_loaded;

bool start_use_color(void)
{
	const char *term;

	if (!isatty(STDOUT_FILENO))
		return false;
	if (getenv("NO_COLOR"))
		return false;
	term = getenv("TERM");
	if (!term || !*term || strcmp(term, "dumb") == 0)
		return false;
	return true;
}

static int load_version_file(const char *path)
{
	char *data;
	size_t len;
	size_t i;

	data = tam_fs_read_file(path, &len);
	if (!data)
		return -1;
	while (len > 0 && (data[len - 1] == '\n' || data[len - 1] == '\r' ||
			   data[len - 1] == ' ' || data[len - 1] == '\t'))
		len--;
	if (len == 0 || len >= sizeof(g_version)) {
		free(data);
		return -1;
	}
	memcpy(g_version, data, len);
	g_version[len] = '\0';
	for (i = 0; i < len; i++) {
		if (!isprint((unsigned char)g_version[i])) {
			free(data);
			g_version[0] = '\0';
			return -1;
		}
	}
	free(data);
	return 0;
}

const char *start_version(void)
{
	char *path;
	const char *env;

	if (g_version_loaded)
		return g_version[0] ? g_version : "0.2.5";
	g_version_loaded = 1;

	/* Explicit override wins (tests, packaging trials). */
	env = getenv("START_VERSION");
	if (env && *env) {
		snprintf(g_version, sizeof(g_version), "%s", env);
		return g_version;
	}

	path = start_find_data_file("VERSION");
	if (path) {
		if (load_version_file(path) == 0) {
			free(path);
			return g_version;
		}
		free(path);
	}
	snprintf(g_version, sizeof(g_version), "0.2.5");
	return g_version;
}

char *start_find_data_file(const char *name)
{
	char *exe = NULL;
	char *dir = NULL;
	char *cand = NULL;
	char link[PATH_MAX];
	ssize_t n;
	const char *env;

	if (strcmp(name, "menu.json") == 0) {
		env = getenv("START_MENU");
		if (env && *env && tam_fs_file_exists(env))
			return strdup(env);
	}

	/* Development: file beside sources / cwd share layout */
	cand = tam_path_join(".", name);
	if (cand && tam_fs_file_exists(cand))
		return cand;
	free(cand);

	cand = tam_path_join("share/start", name);
	if (cand && tam_fs_file_exists(cand))
		return cand;
	free(cand);

	n = readlink("/proc/self/exe", link, sizeof(link) - 1);
	if (n > 0) {
		char *slash;

		link[n] = '\0';
		exe = strdup(link);
		if (exe) {
			slash = strrchr(exe, '/');
			if (slash) {
				*slash = '\0';
				/* PREFIX/bin/start -> PREFIX/share/start/name */
				dir = tam_path_join(exe, "../share/start");
				if (dir) {
					cand = tam_path_join(dir, name);
					free(dir);
					if (cand && tam_fs_file_exists(cand)) {
						free(exe);
						return cand;
					}
					free(cand);
				}
				/* Development: menu.json beside binary parent */
				cand = tam_path_join(exe, name);
				if (cand && tam_fs_file_exists(cand)) {
					free(exe);
					return cand;
				}
				free(cand);
				/* Development tree: commands/start/menu.json next to build/ */
				dir = tam_path_join(exe, "..");
				if (dir) {
					cand = tam_path_join(dir, name);
					free(dir);
					if (cand && tam_fs_file_exists(cand)) {
						free(exe);
						return cand;
					}
					free(cand);
				}
			}
			free(exe);
		}
	}

	cand = strdup("/usr/share/start");
	if (cand) {
		char *full = tam_path_join(cand, name);
		free(cand);
		if (full && tam_fs_file_exists(full))
			return full;
		free(full);
	}
	cand = strdup("/usr/local/share/start");
	if (cand) {
		char *full = tam_path_join(cand, name);
		free(cand);
		if (full && tam_fs_file_exists(full))
			return full;
		free(full);
	}
	return NULL;
}

bool start_command_on_path(const char *cmd)
{
	const char *path;
	char *copy;
	char *save;
	char *tok;
	char *full;
	bool found = false;

	if (!cmd || !*cmd)
		return false;
	if (strchr(cmd, '/'))
		return access(cmd, X_OK) == 0;

	path = getenv("PATH");
	if (!path || !*path)
		path = "/usr/bin:/bin";
	copy = strdup(path);
	if (!copy)
		return false;
	for (tok = strtok_r(copy, ":", &save); tok; tok = strtok_r(NULL, ":", &save)) {
		full = tam_path_join(tok, cmd);
		if (full && access(full, X_OK) == 0) {
			found = true;
			free(full);
			break;
		}
		free(full);
	}
	free(copy);
	return found;
}

size_t start_visible_len(const char *text)
{
	size_t n = 0;
	const unsigned char *p = (const unsigned char *)text;

	while (*p) {
		if (*p == 0x1b && p[1] == '[') {
			p += 2;
			while (*p && !(*p >= '@' && *p <= '~'))
				p++;
			if (*p)
				p++;
			continue;
		}
		/* Count UTF-8 code points as one column (UI strings are ASCII or
		 * single-width punctuation). Skip continuation bytes. */
		if ((*p & 0xc0) == 0x80) {
			p++;
			continue;
		}
		n++;
		p++;
	}
	return n;
}

void start_strip_ansi(char *dst, size_t dstsz, const char *src)
{
	size_t o = 0;
	const unsigned char *p = (const unsigned char *)src;

	if (!dstsz)
		return;
	while (*p && o + 1 < dstsz) {
		if (*p == 0x1b && p[1] == '[') {
			p += 2;
			while (*p && !(*p >= '@' && *p <= '~'))
				p++;
			if (*p)
				p++;
			continue;
		}
		dst[o++] = (char)*p++;
	}
	dst[o] = '\0';
}

void start_clip_pad(char *dst, size_t dstsz, const char *text, int width)
{
	char plain[1024];
	size_t vis;
	int i;

	if (width < 1 || dstsz < 2) {
		if (dstsz)
			dst[0] = '\0';
		return;
	}
	vis = start_visible_len(text);
	if ((int)vis > width) {
		start_strip_ansi(plain, sizeof(plain), text);
		if (width == 1) {
			snprintf(dst, dstsz, ".");
			return;
		}
		/* ASCII ellipsis: three dots if room, else one. Avoid UTF-8
		 * width bugs that can steal columns from the footer version. */
		if (width >= 4) {
			plain[width - 3] = '\0';
			snprintf(dst, dstsz, "%s...", plain);
		} else {
			plain[width - 1] = '\0';
			snprintf(dst, dstsz, "%s.", plain);
		}
		return;
	}
	snprintf(dst, dstsz, "%s", text);
	vis = start_visible_len(dst);
	for (i = (int)vis; i < width && strlen(dst) + 1 < dstsz; i++)
		strcat(dst, " ");
}

void start_terminal_size(int *cols, int *rows)
{
	struct winsize ws;

	*cols = 80;
	*rows = 24;
	if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0) {
		if (ws.ws_col > 0)
			*cols = ws.ws_col;
		if (ws.ws_row > 0)
			*rows = ws.ws_row;
	}
	if (*cols < 40)
		*cols = 40;
	if (*rows < 8)
		*rows = 8;
}

int start_page_capacity(int rows)
{
	int cap = rows - START_CHROME_TOP - START_CHROME_BOTTOM;
	return cap < 1 ? 1 : cap;
}

const char *start_sgr_bold(void)
{
	return start_use_color() ? "\033[1m" : "";
}

const char *start_sgr_dim(void)
{
	return start_use_color() ? "\033[2m" : "";
}

const char *start_sgr_cyan(void)
{
	return start_use_color() ? "\033[36m" : "";
}

const char *start_sgr_green(void)
{
	return start_use_color() ? "\033[32m" : "";
}

const char *start_sgr_yellow(void)
{
	return start_use_color() ? "\033[33m" : "";
}

const char *start_sgr_reset(void)
{
	return start_use_color() ? "\033[0m" : "";
}

const char *start_attention_on(void)
{
	const char *term;
	const char *colorterm;

	if (!start_use_color())
		return "";
	term = getenv("TERM");
	colorterm = getenv("COLORTERM");
	if ((term && strstr(term, "256color")) ||
	    (colorterm && (strcmp(colorterm, "truecolor") == 0 ||
			   strcmp(colorterm, "24bit") == 0)))
		return "\033[38;5;15m\033[48;5;236m";
	return "\033[7m";
}

const char *start_attention_off(void)
{
	return start_use_color() ? "\033[0m" : "";
}
