#define _POSIX_C_SOURCE 200809L

#include "version.h"

#include <magic.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>

#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <unistd.h>

static int want_edit = 0;

static void failf(const char *fmt, ...)
{
	va_list ap;
	fputs("tam-open: ", stderr);
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fputc('\n', stderr);
}

static int tool_exists(const char *name)
{
	char *path;
	char *copy;
	char *dir;
	size_t len;

	if (!name || !*name)
		return 0;
	if (strchr(name, '/'))
		return access(name, X_OK) == 0;

	path = getenv("PATH");
	if (!path || !*path)
		path = "/usr/local/bin:/usr/bin:/bin";
	copy = strdup(path);
	if (!copy)
		return 0;
	for (dir = strtok(copy, ":"); dir; dir = strtok(NULL, ":")) {
		char candidate[PATH_MAX];
		if (!*dir)
			continue;
		len = snprintf(candidate, sizeof(candidate), "%s/%s", dir, name);
		if (len >= sizeof(candidate))
			continue;
		if (access(candidate, X_OK) == 0) {
			free(copy);
			return 1;
		}
	}
	free(copy);
	return 0;
}

static char *lower_copy(const char *s)
{
	size_t n = strlen(s);
	char *out = malloc(n + 1);
	size_t i;
	if (!out)
		return NULL;
	for (i = 0; i < n; i++)
		out[i] = (char)tolower((unsigned char)s[i]);
	out[n] = '\0';
	return out;
}

static int is_graphical(void)
{
	const char *wayland = getenv("WAYLAND_DISPLAY");
	const char *display = getenv("DISPLAY");
	return (wayland && *wayland) || (display && *display);
}

static int is_url(const char *s)
{
	size_t i;

	if (!strncasecmp(s, "http://", 7) || !strncasecmp(s, "https://", 8) ||
	    !strncasecmp(s, "file://", 7))
		return 1;
	if (!isalpha((unsigned char)s[0]))
		return 0;
	for (i = 1; s[i] && s[i] != ':'; i++) {
		unsigned char c = (unsigned char)s[i];
		if (!isalnum(c) && c != '+' && c != '-' && c != '.')
			return 0;
		if (i > 63)
			return 0;
	}
	return s[i] == ':';
}

static char *strip_file_url(const char *s)
{
	const char *p = s;
	if (!strncasecmp(s, "file://", 7)) {
		p = s + 7;
		if (!strncasecmp(p, "localhost/", 10))
			p += 9;
	}
	return strdup(p);
}

static int run_foreground(char *const argv[])
{
	pid_t pid = fork();
	int status;

	if (pid < 0) {
		failf("could not start %s: %s", argv[0], strerror(errno));
		return 127;
	}
	if (pid == 0) {
		execvp(argv[0], argv);
		fprintf(stderr, "tam-open: %s: %s\n", argv[0], strerror(errno));
		_exit(127);
	}
	if (waitpid(pid, &status, 0) < 0) {
		failf("could not wait for %s: %s", argv[0], strerror(errno));
		return 127;
	}
	if (WIFEXITED(status))
		return WEXITSTATUS(status);
	if (WIFSIGNALED(status))
		return 128 + WTERMSIG(status);
	return 1;
}

static int run_pipeline(char *const first[], char *const second[])
{
	int fd[2];
	pid_t p1, p2;
	int status1 = 0, status2 = 0;

	if (!second || !second[0])
		return run_foreground(first);

	if (pipe(fd) < 0) {
		failf("could not create pipe: %s", strerror(errno));
		return 127;
	}
	p1 = fork();
	if (p1 < 0) {
		failf("could not start %s: %s", first[0], strerror(errno));
		close(fd[0]);
		close(fd[1]);
		return 127;
	}
	if (p1 == 0) {
		close(fd[0]);
		if (dup2(fd[1], STDOUT_FILENO) < 0)
			_exit(127);
		close(fd[1]);
		execvp(first[0], first);
		fprintf(stderr, "tam-open: %s: %s\n", first[0], strerror(errno));
		_exit(127);
	}
	p2 = fork();
	if (p2 < 0) {
		failf("could not start %s: %s", second[0], strerror(errno));
		close(fd[0]);
		close(fd[1]);
		waitpid(p1, NULL, 0);
		return 127;
	}
	if (p2 == 0) {
		close(fd[1]);
		if (dup2(fd[0], STDIN_FILENO) < 0)
			_exit(127);
		close(fd[0]);
		execvp(second[0], second);
		fprintf(stderr, "tam-open: %s: %s\n", second[0], strerror(errno));
		_exit(127);
	}
	close(fd[0]);
	close(fd[1]);
	waitpid(p1, &status1, 0);
	waitpid(p2, &status2, 0);
	if (WIFEXITED(status1) && WEXITSTATUS(status1) != 0)
		return WEXITSTATUS(status1);
	if (WIFEXITED(status2))
		return WEXITSTATUS(status2);
	return 1;
}

static int detach_spawn(char *const argv[])
{
	pid_t pid = fork();

	if (pid < 0) {
		failf("could not start %s: %s", argv[0], strerror(errno));
		return -1;
	}
	if (pid == 0) {
		int dev;
		setsid();
		dev = open("/dev/null", O_RDWR);
		if (dev >= 0) {
			dup2(dev, STDIN_FILENO);
			dup2(dev, STDOUT_FILENO);
			dup2(dev, STDERR_FILENO);
			if (dev > 2)
				close(dev);
		}
		execvp(argv[0], argv);
		_exit(127);
	}
	return 0;
}

static int run_editor(const char *target)
{
	const char *editor_env = getenv("EDITOR");
	char *copy = NULL;
	char *argv[8];
	int i = 0;
	char *token;

	if (editor_env && *editor_env) {
		copy = strdup(editor_env);
		if (copy) {
			for (token = strtok(copy, " \t"); token && i < 7; token = strtok(NULL, " \t"))
				argv[i++] = token;
			argv[i] = (char *)target;
			argv[i + 1] = NULL;
			if (i > 0 && tool_exists(argv[0])) {
				int rc = run_foreground(argv);
				free(copy);
				return rc;
			}
			free(copy);
		}
	}
	argv[0] = "micro";
	argv[1] = (char *)target;
	argv[2] = NULL;
	if (!tool_exists("micro")) {
		failf("no text editor found: install micro or set EDITOR");
		return 127;
	}
	return run_foreground(argv);
}

static int is_text_bytes(const unsigned char *buf, size_t n)
{
	size_t i;
	int saw_nul = 0;

	for (i = 0; i < n; i++) {
		if (buf[i] == 0) {
			saw_nul = 1;
			break;
		}
	}
	if (saw_nul)
		return 0;

	/* Strict-ish UTF-8 validation. */
	i = 0;
	while (i < n) {
		unsigned char c = buf[i];
		size_t len = 0;
		size_t j;
		if (c < 0x80) {
			if (c == '\t' || c == '\n' || c == '\r' || c == '\f' || c >= 0x20)
				len = 1;
			else
				return 0;
		} else if ((c & 0xE0) == 0xC0) {
			len = 2;
		} else if ((c & 0xF0) == 0xE0) {
			len = 3;
		} else if ((c & 0xF8) == 0xF0) {
			len = 4;
		} else {
			return 0;
		}
		if (len > 1) {
			if (i + len > n)
				return 0;
			for (j = 1; j < len; j++) {
				if ((buf[i + j] & 0xC0) != 0x80)
					return 0;
			}
		}
		i += len ? len : 1;
	}
	return 1;
}

static int file_is_text(const char *path, const char *mime)
{
	FILE *f;
	unsigned char buf[65536];
	size_t n;

	if (mime && (!strncasecmp(mime, "text/", 5) ||
	             !strcmp(mime, "application/json") ||
	             !strcmp(mime, "application/xml") ||
	             !strcmp(mime, "application/javascript") ||
	             !strcmp(mime, "application/x-shellscript")))
		return 1;

	f = fopen(path, "rb");
	if (!f)
		return 0;
	n = fread(buf, 1, sizeof(buf), f);
	fclose(f);
	if (n == 0)
		return 1;
	return is_text_bytes(buf, n);
}

static char *file_mime(const char *path)
{
	magic_t cookie = magic_open(MAGIC_MIME_TYPE);
	const char *result;
	char *copy;

	if (!cookie)
		return NULL;
	if (magic_load(cookie, NULL) != 0) {
		magic_close(cookie);
		return NULL;
	}
	result = magic_file(cookie, path);
	copy = result ? strdup(result) : NULL;
	magic_close(cookie);
	return copy;
}

static char *lower_ext(const char *path)
{
	const char *dot = strrchr(path, '.');
	if (!dot || !dot[1])
		return strdup("");
	return lower_copy(dot + 1);
}

static int has_ext(const char *ext, const char *list)
{
	/* list is comma-separated */
	char *copy = strdup(list);
	char *tok;
	int found = 0;
	if (!copy)
		return 0;
	for (tok = strtok(copy, ","); tok; tok = strtok(NULL, ",")) {
		if (!strcmp(tok, ext)) {
			found = 1;
			break;
		}
	}
	free(copy);
	return found;
}

static int is_archive_ext(const char *ext)
{
	return has_ext(ext, "tar,gz,tgz,zip,zst,zstd,cpio,7z,xz,bz2,tbz2,lz,lrz");
}

static int is_archive_mime(const char *mime)
{
	if (!mime)
		return 0;
	return strstr(mime, "zip") || strstr(mime, "tar") || strstr(mime, "gzip") ||
	       strstr(mime, "x-7z") || strstr(mime, "x-cpio") || strstr(mime, "zstd") ||
	       strstr(mime, "x-xz") || strstr(mime, "x-bzip");
}

static int detach_browser(const char *url)
{
	char *argv[8];
	int i = 0;

	if (tool_exists("tam-launch-browser")) {
		argv[i++] = "tam-launch-browser";
		argv[i++] = (char *)url;
		argv[i] = NULL;
		return detach_spawn(argv);
	}

	{
		const char *browser = getenv("BROWSER");
		if (browser && *browser && tool_exists(browser)) {
			argv[i++] = (char *)browser;
			argv[i++] = (char *)url;
			argv[i] = NULL;
			return detach_spawn(argv);
		}
	}

	{
		static const char *candidates[] = {
			"chromium", "google-chrome-stable", "google-chrome",
			"firefox", "brave", "vivaldi", "zen-browser", NULL
		};
		int c;
		for (c = 0; candidates[c]; c++) {
			if (tool_exists(candidates[c])) {
				argv[0] = (char *)candidates[c];
				argv[1] = (char *)url;
				argv[2] = NULL;
				return detach_spawn(argv);
			}
		}
	}

	failf("no graphical browser found in PATH");
	return 127;
}

static int run_terminal_browser(const char *url)
{
	static const char *candidates[] = { "lynx", "w3m", "links", NULL };
	int c;
	char *argv[4];
	for (c = 0; candidates[c]; c++) {
		if (tool_exists(candidates[c])) {
			argv[0] = (char *)candidates[c];
			argv[1] = (char *)url;
			argv[2] = NULL;
			return run_foreground(argv);
		}
	}
	failf("no terminal browser found in PATH (tried lynx, w3m, links)");
	return 127;
}

static int open_directory(const char *target, int graphical)
{
	if (graphical) {
		char *argv[4];
		if (tool_exists("tam-launch-nautilus")) {
			argv[0] = "tam-launch-nautilus";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		if (tool_exists("xdg-open")) {
			argv[0] = "xdg-open";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		failf("no file manager found for directory: %s", target);
		return 127;
	}
	{
		char *argv[6];
		argv[0] = "ls";
		argv[1] = "-la";
		argv[2] = "--";
		argv[3] = (char *)target;
		argv[4] = NULL;
		if (!tool_exists("ls")) {
			failf("ls is required to list directories");
			return 127;
		}
		return run_foreground(argv);
	}
}

static int open_pdf(const char *target, int graphical)
{
	if (graphical) {
		char *argv[4];
		static const char *candidates[] = { "zathura", "evince", NULL };
		int c;
		for (c = 0; candidates[c]; c++) {
			if (tool_exists(candidates[c])) {
				argv[0] = (char *)candidates[c];
				argv[1] = (char *)target;
				argv[2] = NULL;
				return detach_spawn(argv);
			}
		}
		if (tool_exists("chromium")) {
			argv[0] = "chromium";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		failf("no PDF viewer found in PATH (tried zathura, evince, chromium)");
		return 127;
	}
	if (tool_exists("pdftotext")) {
		char *first[5];
		char *second[3];
		first[0] = "pdftotext";
		first[1] = (char *)target;
		first[2] = "-";
		first[3] = NULL;
		if (tool_exists("less")) {
			second[0] = "less";
			second[1] = NULL;
			return run_pipeline(first, second);
		}
		return run_foreground(first);
	}
	failf("cannot display PDF in a text console: install pdftotext");
	return 127;
}

static int open_image(const char *target, int graphical)
{
	if (graphical) {
		char *argv[4];
		if (tool_exists("imv")) {
			argv[0] = "imv";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		if (tool_exists("xdg-open")) {
			argv[0] = "xdg-open";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		failf("no image viewer found in PATH (tried imv)");
		return 127;
	}
	{
		static const char *candidates[] = { "chafa", "viu", "timg", NULL };
		int c;
		for (c = 0; candidates[c]; c++) {
			if (tool_exists(candidates[c])) {
				char *argv[4];
				argv[0] = (char *)candidates[c];
				argv[1] = (char *)target;
				argv[2] = NULL;
				return run_foreground(argv);
			}
		}
	}
	failf("cannot display images in a text console: install chafa or viu");
	return 127;
}

static int open_media(const char *target, int graphical, int is_video)
{
	char *argv[6];
	if (graphical) {
		if (tool_exists("mpv")) {
			argv[0] = "mpv";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		if (tool_exists("xdg-open")) {
			argv[0] = "xdg-open";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return detach_spawn(argv);
		}
		failf("no media player found in PATH (tried mpv)");
		return 127;
	}
	if (!is_video && tool_exists("mpv")) {
		argv[0] = "mpv";
		argv[1] = "--no-video";
		argv[2] = (char *)target;
		argv[3] = NULL;
		return run_foreground(argv);
	}
	failf("video playback requires a graphical session");
	return 127;
}

static int open_archive(const char *target)
{
	if (tool_exists("bsdtar")) {
		char *argv[5];
		argv[0] = "bsdtar";
		argv[1] = "-tvf";
		argv[2] = (char *)target;
		argv[3] = NULL;
		if (tool_exists("less")) {
			char *first[4];
			char *second[3];
			first[0] = "bsdtar"; first[1] = "-tvf"; first[2] = (char *)target; first[3] = NULL;
			second[0] = "less"; second[1] = NULL;
			return run_pipeline(first, second);
		}
		return run_foreground(argv);
	}
	if (tool_exists("7z")) {
		char *argv[4];
		argv[0] = "7z";
		argv[1] = "l";
		argv[2] = (char *)target;
		argv[3] = NULL;
		return run_foreground(argv);
	}
	failf("no archive lister found in PATH (tried bsdtar, 7z)");
	return 127;
}

static int open_binary(const char *target)
{
	if (want_edit) {
		char *argv[4];
		if (tool_exists("hexedit")) {
			argv[0] = "hexedit";
			argv[1] = (char *)target;
			argv[2] = NULL;
			return run_foreground(argv);
		}
		failf("hexedit is not installed");
		return 127;
	}
	if (tool_exists("hexyl")) {
		char *first[3];
		char *second[3];
		first[0] = "hexyl";
		first[1] = (char *)target;
		first[2] = NULL;
		if (tool_exists("less")) {
			second[0] = "less";
			second[1] = "-R";
			second[2] = NULL;
			return run_pipeline(first, second);
		}
		return run_foreground(first);
	}
	if (tool_exists("xxd") && tool_exists("less")) {
		char *first[4];
		char *second[3];
		first[0] = "xxd";
		first[1] = (char *)target;
		first[2] = NULL;
		second[0] = "less";
		second[1] = NULL;
		return run_pipeline(first, second);
	}
	if (tool_exists("od")) {
		char *argv[7];
		argv[0] = "od";
		argv[1] = "-An";
		argv[2] = "-tx1";
		argv[3] = "-v";
		argv[4] = (char *)target;
		argv[5] = NULL;
		if (tool_exists("less")) {
			char *first[6];
			char *second[3];
			first[0] = "od"; first[1] = "-An"; first[2] = "-tx1"; first[3] = "-v";
			first[4] = (char *)target; first[5] = NULL;
			second[0] = "less"; second[1] = NULL;
			return run_pipeline(first, second);
		}
		return run_foreground(argv);
	}
	failf("no hex viewer found in PATH (tried hexyl, xxd, od)");
	return 127;
}

static int handle_target(const char *target, int graphical)
{
	struct stat st;
	char *mime = NULL;
	char *ext = NULL;
	int rc = 0;

	if (stat(target, &st) != 0) {
		failf("cannot stat %s: %s", target, strerror(errno));
		return 1;
	}
	if (S_ISDIR(st.st_mode))
		return open_directory(target, graphical);
	if (!S_ISREG(st.st_mode)) {
		failf("not a regular file or directory: %s", target);
		return 1;
	}

	mime = file_mime(target);
	ext = lower_ext(target);

	if (is_url(target)) {
		/* Already converted from file:// before reaching here. */
	}

	if (!strncasecmp(mime ? mime : "", "application/pdf", 15) || !strcmp(ext, "pdf")) {
		rc = open_pdf(target, graphical);
	} else if (!strncasecmp(mime ? mime : "", "image/", 6)) {
		rc = open_image(target, graphical);
	} else if (!strncasecmp(mime ? mime : "", "audio/", 6)) {
		rc = open_media(target, graphical, 0);
	} else if (!strncasecmp(mime ? mime : "", "video/", 6)) {
		rc = open_media(target, graphical, 1);
	} else if (!strncasecmp(mime ? mime : "", "text/html", 9) ||
	           !strcmp(ext, "html") || !strcmp(ext, "htm")) {
		if (graphical)
			rc = detach_browser(target);
		else
			rc = run_terminal_browser(target);
	} else if (is_archive_mime(mime) || is_archive_ext(ext)) {
		rc = open_archive(target);
	} else if (file_is_text(target, mime)) {
		rc = run_editor(target);
	} else {
		/* Unknown binary. */
		if (tool_exists("xdg-open") && graphical) {
			char *argv[4];
			argv[0] = "xdg-open";
			argv[1] = (char *)target;
			argv[2] = NULL;
			rc = detach_spawn(argv);
		} else {
			rc = open_binary(target);
		}
	}

	if (rc != 0 && mime)
		failf("detected type: %s", mime);

	free(mime);
	free(ext);
	return rc;
}

static void usage(FILE *out)
{
	fputs("Usage: tam-open [--edit] [--version|-v] [--help] [--] <path-or-url>\n"
	      "Open a file, directory, or URL for inspection.\n"
	      "Graphical viewers detach; terminal tools run in the foreground.\n",
	      out);
}

int main(int argc, char **argv)
{
	int i;
	const char *target = NULL;
	int graphical;

	for (i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) {
			usage(stdout);
			return 0;
		}
		if (!strcmp(argv[i], "--version") || !strcmp(argv[i], "-v")) {
			puts(TAM_OPEN_VERSION);
			return 0;
		}
		if (!strcmp(argv[i], "--edit")) {
			want_edit = 1;
			continue;
		}
		if (!strcmp(argv[i], "--")) {
			if (i + 1 < argc && !target) {
				target = argv[++i];
				continue;
			}
			failf("missing target after --");
			usage(stderr);
			return 1;
		}
		if (argv[i][0] == '-') {
			failf("unknown option %s", argv[i]);
			usage(stderr);
			return 1;
		}
		if (target) {
			failf("only one target is supported");
			usage(stderr);
			return 1;
		}
		target = argv[i];
	}

	if (!target) {
		usage(stderr);
		return 1;
	}

	graphical = is_graphical();

	if (is_url(target) && strncasecmp(target, "file://", 7) == 0) {
		char *path = strip_file_url(target);
		if (!path) {
			failf("out of memory");
			return 1;
		}
		int rc = handle_target(path, graphical);
		free(path);
		return rc;
	}

	if (is_url(target)) {
		if (graphical)
			return detach_browser(target);
		return run_terminal_browser(target);
	}

	return handle_target(target, graphical);
}
