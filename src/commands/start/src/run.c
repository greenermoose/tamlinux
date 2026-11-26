#include "run.h"

#include "util.h"

#include <tam.h>

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static char *which_path(const char *cmd)
{
	return tam_which(cmd);
}

static int run_argv(char *const argv[])
{
	/* start ignores Ctrl+C and Ctrl+\ while the activity runs, so they
	 * reach only the activity. */
	int code = 1;
	if (tam_run_foreground((const char *const *)argv, &code) < 0) {
		if (errno == ENOENT)
			return 127;
		perror("start: run");
		return 1;
	}
	return code;
}

static int resolve_and_run(const start_activity_t *item)
{
	char *argv_buf[START_MAX_ARGV + 4];
	int argc = 0;
	int i;

	if (strcmp(item->id, "pmars") == 0) {
		char *exe = which_path("pmars");
		if (exe) {
			char *slash = strrchr(exe, '/');
			char *prefix = NULL;
			char *w1 = NULL;
			char *w2 = NULL;

			if (slash) {
				*slash = '\0';
				slash = strrchr(exe, '/');
				if (slash) {
					*slash = '\0';
					prefix = strdup(exe);
				}
			}
			free(exe);
			if (prefix) {
				char *warriors = tam_path_join(prefix, "share/pmars/warriors");
				free(prefix);
				if (warriors) {
					w1 = tam_path_join(warriors, "excalibur.red");
					w2 = tam_path_join(warriors, "sonofvain.red");
					free(warriors);
				}
			}
			if (w1 && w2 && tam_fs_file_exists(w1) && tam_fs_file_exists(w2)) {
				int rc;

				argv_buf[0] = "pmars";
				argv_buf[1] = "-e";
				argv_buf[2] = w1;
				argv_buf[3] = w2;
				argv_buf[4] = NULL;
				rc = run_argv(argv_buf);
				free(w1);
				free(w2);
				return rc;
			}
			free(w1);
			free(w2);
		}
	} else if (strcmp(item->id, "frotz") == 0) {
		char story[PATH_MAX];
		char expanded[PATH_MAX];
		char *line = NULL;
		size_t n = 0;
		ssize_t r;

		fputs("\nFrotz Z-machine interpreter (.z3/.z5/.z8/.zblorb story file required).\n",
		      stdout);
		fputs("Story file path (or Enter to show version and return): ", stdout);
		fflush(stdout);
		r = getline(&line, &n, stdin);
		if (r < 0) {
			free(line);
			fputc('\n', stdout);
			return 0;
		}
		while (r > 0 && (line[r - 1] == '\n' || line[r - 1] == '\r'))
			line[--r] = '\0';
		if (r == 0) {
			free(line);
			argv_buf[0] = "frotz";
			argv_buf[1] = "-v";
			argv_buf[2] = NULL;
			return run_argv(argv_buf);
		}
		snprintf(story, sizeof(story), "%s", line);
		free(line);
		if (story[0] == '~' && (story[1] == '/' || story[1] == '\0')) {
			const char *home = getenv("HOME");
			if (!home)
				home = "";
			snprintf(expanded, sizeof(expanded), "%s%s", home, story + 1);
		} else {
			snprintf(expanded, sizeof(expanded), "%s", story);
		}
		if (!tam_fs_file_exists(expanded)) {
			fprintf(stdout, "%s%sNotice:%s Story file not found: %s\n",
				start_sgr_bold(), start_sgr_yellow(), start_sgr_reset(),
				expanded);
			return 1;
		}
		argv_buf[0] = "frotz";
		argv_buf[1] = expanded;
		argv_buf[2] = NULL;
		return run_argv(argv_buf);
	}

	for (i = 0; i < item->argc && i < START_MAX_ARGV; i++)
		argv_buf[argc++] = item->argv[i];
	argv_buf[argc] = NULL;
	return run_argv(argv_buf);
}

int start_run_activity(const start_activity_t *item)
{
	if (!start_command_on_path(item->check)) {
		fprintf(stdout, "\n%s%sNotice:%s '%s' is not currently installed.\n",
			start_sgr_bold(), start_sgr_yellow(), start_sgr_reset(),
			item->check);
		if (strcmp(item->category, "Curated Games & Simulations") == 0) {
			fputs("To include the curated games/simulations set in your Tamlinux profile,\n",
			      stdout);
			fputs("enable the package set in your configuration:\n", stdout);
			fprintf(stdout, "  %stamlinux.terminalGames.enable = true;%s\n",
				start_sgr_bold(), start_sgr_reset());
			fputs("or install the package via Arch/Nix.\n", stdout);
		}
		return 1;
	}
	return resolve_and_run(item);
}
