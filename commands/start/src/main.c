#include "frame.h"
#include "input.h"
#include "menu.h"
#include "run.h"
#include "screen.h"
#include "util.h"

#include <tam.h>

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

static void usage(FILE *out)
{
	fputs("Usage: start [--list] [--check] [--version|-V] [--help|-h]\n"
	      "First text-login workstation activities menu (D215).\n"
	      "Choose what to start doing; Esc (or Backspace/Delete) returns to the shell.\n"
	      "Opening the menu never starts graphics.\n",
	      out);
}

static int cmd_list(const start_menu_t *menu)
{
	size_t i;

	printf("%-8s %-16s %-25s %-10s %s\n", "Letter", "ID", "Command", "Installed",
	       "Description");
	fputs("──────────────────────────────────────────────────────────────────────────────────────────\n",
	      stdout);
	for (i = 0; i < menu->count; i++) {
		const start_activity_t *a = &menu->items[i];
		char cmd[256];
		size_t o = 0;
		int j;

		cmd[0] = '\0';
		for (j = 0; j < a->argc; j++) {
			size_t n = strlen(a->argv[j]);
			if (o && o + 1 < sizeof(cmd))
				cmd[o++] = ' ';
			if (o + n < sizeof(cmd)) {
				memcpy(cmd + o, a->argv[j], n);
				o += n;
				cmd[o] = '\0';
			}
		}
		printf("%-8c %-16s %-25s %-10s %s\n", a->letter, a->id, cmd,
		       start_command_on_path(a->check) ? "yes" : "no", a->description);
	}
	return 0;
}

static int cmd_check(const start_menu_t *menu)
{
	size_t i;
	size_t installed = 0;

	for (i = 0; i < menu->count; i++) {
		const start_activity_t *a = &menu->items[i];
		int ok = start_command_on_path(a->check);

		if (ok)
			installed++;
		printf(" %s [%c] %s (%s)\n",
		       ok ? (start_use_color() ? "\033[32m✓\033[0m" : "✓")
			  : (start_use_color() ? "\033[2m✗\033[0m" : "✗"),
		       a->letter, a->label, a->check);
	}
	printf("\n%zu/%zu activities installed on this system.\n", installed, menu->count);
	printf("v%s\n", start_version());
	return 0;
}

static void free_frame(char **lines, size_t height)
{
	size_t i;

	for (i = 0; i < height; i++)
		free(lines[i]);
}

static int interactive_loop(start_menu_t *menu)
{
	struct termios old;
	struct termios raw;
	start_screen_t screen;
	int attention = 0;
	size_t page_index = 0;
	int fd = STDIN_FILENO;
	volatile int restored = 0;

	if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO)) {
		fputs("start: interactive menu requires a terminal\n", stderr);
		return 1;
	}
	if (tcgetattr(fd, &old) != 0) {
		perror("start: tcgetattr");
		return 1;
	}
	raw = old;
	/* cbreak: byte-at-a-time, no echo; keep signals and output processing */
	raw.c_lflag &= (tcflag_t)~(ICANON | ECHO);
	raw.c_cc[VMIN] = 1;
	raw.c_cc[VTIME] = 0;
	if (tcsetattr(fd, TCSADRAIN, &raw) != 0) {
		perror("start: tcsetattr");
		return 1;
	}

	start_screen_init(&screen, NULL, NULL, NULL);
	start_screen_enter(&screen);

	while (1) {
		int width;
		int rows;
		size_t page_starts[64];
		size_t page_lens[64];
		size_t page_count;
		size_t cap;
		int on_page[START_MAX_ACTIVITIES];
		size_t on_n;
		char **frame;
		char key[32];
		const start_row_t *page;
		size_t plen;
		int run_rc = -1;

		start_terminal_size(&width, &rows);
		cap = (size_t)start_page_capacity(rows);
		page_count = start_menu_paginate(menu->rows, menu->row_count, (int)cap,
						 page_starts, page_lens);
		if (page_index >= page_count)
			page_index = page_count - 1;
		page = menu->rows + page_starts[page_index];
		plen = page_lens[page_index];
		on_n = start_choice_indices_on_page(menu->rows, page_starts[page_index],
						    plen, on_page, START_MAX_ACTIVITIES);
		{
			int found = 0;
			size_t k;

			for (k = 0; k < on_n; k++) {
				if (on_page[k] == attention) {
					found = 1;
					break;
				}
			}
			if (!found && on_n)
				attention = on_page[0];
		}

		frame = calloc((size_t)rows, sizeof(char *));
		if (!frame)
			break;
		start_compose_frame(frame, (size_t)rows, width, page, plen, attention);
		start_screen_update(&screen, frame, (size_t)rows, width);
		free_frame(frame, (size_t)rows);
		free(frame);

		if (start_read_key(fd, key, sizeof(key)) != 0)
			break;

		if (strcmp(key, START_KEY_ESC) == 0 ||
		    strcmp(key, START_KEY_BACKSPACE) == 0 ||
		    strcmp(key, START_KEY_DELETE) == 0) {
			break;
		}
		if (strcmp(key, START_KEY_UP) == 0) {
			if (attention > 0) {
				size_t pi;

				attention--;
				for (pi = 0; pi < page_count; pi++) {
					int idxs[START_MAX_ACTIVITIES];
					size_t nn = start_choice_indices_on_page(
						menu->rows, page_starts[pi], page_lens[pi],
						idxs, START_MAX_ACTIVITIES);
					size_t k;

					for (k = 0; k < nn; k++) {
						if (idxs[k] == attention) {
							page_index = pi;
							break;
						}
					}
				}
			}
			continue;
		}
		if (strcmp(key, START_KEY_DOWN) == 0) {
			if (attention < (int)menu->count - 1) {
				size_t pi;

				attention++;
				for (pi = 0; pi < page_count; pi++) {
					int idxs[START_MAX_ACTIVITIES];
					size_t nn = start_choice_indices_on_page(
						menu->rows, page_starts[pi], page_lens[pi],
						idxs, START_MAX_ACTIVITIES);
					size_t k;

					for (k = 0; k < nn; k++) {
						if (idxs[k] == attention) {
							page_index = pi;
							break;
						}
					}
				}
			}
			continue;
		}
		if (strcmp(key, START_KEY_PGDN) == 0 || strcmp(key, START_KEY_SPACE) == 0) {
			if (page_count > 1 && page_index + 1 < page_count) {
				int idxs[START_MAX_ACTIVITIES];
				size_t nn;

				page_index++;
				nn = start_choice_indices_on_page(
					menu->rows, page_starts[page_index],
					page_lens[page_index], idxs, START_MAX_ACTIVITIES);
				if (nn)
					attention = idxs[0];
			}
			continue;
		}
		if (strcmp(key, START_KEY_PGUP) == 0 ||
		    strcmp(key, START_KEY_BACKTICK) == 0) {
			if (page_count > 1 && page_index > 0) {
				int idxs[START_MAX_ACTIVITIES];
				size_t nn;

				page_index--;
				nn = start_choice_indices_on_page(
					menu->rows, page_starts[page_index],
					page_lens[page_index], idxs, START_MAX_ACTIVITIES);
				if (nn)
					attention = idxs[0];
			}
			continue;
		}
		if (strcmp(key, START_KEY_HOME) == 0) {
			page_index = 0;
			attention = 0;
			continue;
		}
		if (strcmp(key, START_KEY_END) == 0) {
			page_index = page_count - 1;
			attention = (int)menu->count - 1;
			continue;
		}
		if (strcmp(key, START_KEY_ENTER) == 0 ||
		    strcmp(key, START_KEY_RIGHT) == 0 ||
		    (key[0] && !key[1] && key[0] >= 'a' && key[0] <= 'z' &&
		     start_menu_by_letter(menu, key[0]))) {
			const start_activity_t *item;

			if (strcmp(key, START_KEY_ENTER) == 0 ||
			    strcmp(key, START_KEY_RIGHT) == 0)
				item = &menu->items[attention];
			else
				item = start_menu_by_letter(menu, key[0]);
			start_screen_leave(&screen);
			tcsetattr(fd, TCSADRAIN, &old);
			restored = 1;
			run_rc = start_run_activity(item);
			return run_rc;
		}
	}

	start_screen_leave(&screen);
	if (!restored)
		tcsetattr(fd, TCSADRAIN, &old);
	return 0;
}

static int load_menu(start_menu_t *menu)
{
	char *path = start_find_data_file("menu.json");

	if (!path) {
		fputs("start: cannot find menu.json\n", stderr);
		return -1;
	}
	if (start_menu_load_file(menu, path) != 0) {
		fprintf(stderr, "start: failed to parse %s\n", path);
		free(path);
		return -1;
	}
	free(path);
	return 0;
}

int main(int argc, char **argv)
{
	start_menu_t menu;
	int i;
	int do_list = 0;
	int do_check = 0;

	for (i = 1; i < argc; i++) {
		if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
			usage(stdout);
			return 0;
		}
		if (strcmp(argv[i], "--version") == 0 || strcmp(argv[i], "-V") == 0) {
			printf("start %s\n", start_version());
			return 0;
		}
		if (strcmp(argv[i], "--list") == 0) {
			do_list = 1;
			continue;
		}
		if (strcmp(argv[i], "--check") == 0) {
			do_check = 1;
			continue;
		}
		fprintf(stderr, "start: unknown option %s\n", argv[i]);
		usage(stderr);
		return 1;
	}

	memset(&menu, 0, sizeof(menu));
	if (load_menu(&menu) != 0)
		return 1;

	if (do_list) {
		int rc = cmd_list(&menu);
		start_menu_free(&menu);
		return rc;
	}
	if (do_check) {
		int rc = cmd_check(&menu);
		start_menu_free(&menu);
		return rc;
	}

	{
		int rc = interactive_loop(&menu);
		start_menu_free(&menu);
		return rc;
	}
}
