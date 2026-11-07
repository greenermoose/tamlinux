#include "frame.h"
#include "menu.h"
#include "screen.h"
#include "util.h"

#include <tam.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int failures;

static void expect_true(const char *name, int cond)
{
	if (!cond) {
		fprintf(stderr, "FAIL: %s\n", name);
		failures++;
	} else {
		printf("  ok %s\n", name);
	}
}

static void expect_streq(const char *name, const char *got, const char *want)
{
	if (!got || !want || strcmp(got, want) != 0) {
		fprintf(stderr, "FAIL: %s (got '%s' want '%s')\n", name,
			got ? got : "(null)", want ? want : "(null)");
		failures++;
	} else {
		printf("  ok %s\n", name);
	}
}

static void expect_eq(const char *name, int got, int want)
{
	if (got != want) {
		fprintf(stderr, "FAIL: %s (got %d want %d)\n", name, got, want);
		failures++;
	} else {
		printf("  ok %s\n", name);
	}
}

typedef struct {
	char *blob;
	size_t len;
	size_t cap;
	int flushes;
} capture_t;

static void cap_write(const char *s, void *user)
{
	capture_t *c = user;
	size_t n = strlen(s);

	if (!c->blob || c->len + n + 1 > c->cap) {
		size_t nc = c->cap ? c->cap * 2 : 256;
		char *nb;

		while (nc < c->len + n + 1)
			nc *= 2;
		nb = realloc(c->blob, nc);
		if (!nb)
			return;
		c->blob = nb;
		c->cap = nc;
	}
	memcpy(c->blob + c->len, s, n);
	c->len += n;
	c->blob[c->len] = '\0';
}

static void cap_flush(void *user)
{
	capture_t *c = user;
	c->flushes++;
}

static const char *sample_menu =
	"["
	"{\"id\":\"desktop\",\"category\":\"Graphical Desktop\","
	"\"label\":\"Start graphical desktop shell\",\"check\":\"tam-desktop\","
	"\"argv\":[\"tam-desktop\"],"
	"\"description\":\"Leave the text shell and start the Tamlinux Hyprland desktop\"},"
	"{\"id\":\"hi\",\"category\":\"Orientation & Learning\","
	"\"label\":\"Welcome to Tamlinux\",\"check\":\"tam\","
	"\"argv\":[\"tam\",\"hi\"],"
	"\"description\":\"First-boot orientation and system introduction (invokes tam hi)\"},"
	"{\"id\":\"tam\",\"category\":\"Orientation & Learning\","
	"\"label\":\"Offline Knowledge Guide\",\"check\":\"tam\","
	"\"argv\":[\"tam\"],"
	"\"description\":\"Interactive terminal documentation and learning journeys\"}"
	"]";

static void test_menu_parse(void)
{
	start_menu_t menu;

	expect_eq("load sample", start_menu_load_string(&menu, sample_menu), 0);
	expect_eq("count", (int)menu.count, 3);
	expect_streq("a id", menu.items[0].id, "desktop");
	expect_eq("a letter", menu.items[0].letter, 'a');
	expect_streq("b id", menu.items[1].id, "hi");
	expect_eq("b letter", menu.items[1].letter, 'b');
	expect_eq("desktop argc", menu.items[0].argc, 1);
	expect_eq("hi argc", menu.items[1].argc, 2);
	expect_streq("hi argv1", menu.items[1].argv[1], "hi");
	expect_true("by letter a", start_menu_by_letter(&menu, 'a') == &menu.items[0]);
	start_menu_free(&menu);
}

static void test_paginate(void)
{
	start_menu_t menu;
	size_t starts[16];
	size_t lens[16];
	size_t pages;
	size_t i;

	expect_eq("load", start_menu_load_string(&menu, sample_menu), 0);
	/* rows: header, desktop, header, hi, tam = 5 */
	expect_eq("row count", (int)menu.row_count, 5);
	pages = start_menu_paginate(menu.rows, menu.row_count, 2, starts, lens);
	expect_true("multi page", pages > 1);
	for (i = 0; i < pages; i++)
		expect_true("page len <= 2", (int)lens[i] <= 2);
	expect_eq("page capacity 24", start_page_capacity(24), 24 - 7 - 1);
	expect_eq("page capacity 8", start_page_capacity(8), 1);
	start_menu_free(&menu);
}

static void check_footer_version(const char *semver, int width)
{
	char footer[512];
	char plain[512];
	char expect[64];
	char name[96];

	snprintf(expect, sizeof(expect), "v%s", semver);
	setenv("START_VERSION", semver, 1);
	/* start_version caches; override via env checked first only before
	 * first load — reset by exec. Call format which uses start_version. */
	start_format_footer(footer, sizeof(footer), width);
	start_strip_ansi(plain, sizeof(plain), footer);
	snprintf(name, sizeof(name), "footer %s w=%d contains full version", semver, width);
	expect_true(name, strstr(plain, expect) != NULL);
	snprintf(name, sizeof(name), "footer %s w=%d ends with version", semver, width);
	expect_true(name, strlen(plain) >= strlen(expect) &&
			  strcmp(plain + strlen(plain) - strlen(expect), expect) == 0);
}

static void test_footer(void)
{
	char footer[256];
	char plain[256];
	int widths[] = {40, 48, 65, 80, 100};
	size_t j;

	/* Env override must win before any cached load in this process. */
	setenv("START_VERSION", "0.2.4", 1);
	start_format_footer(footer, sizeof(footer), 80);
	start_strip_ansi(plain, sizeof(plain), footer);
	expect_true("footer starts with hints",
		    strstr(plain, "Down/Up Arrow scroll") != NULL);
	expect_true("footer has Esc quit", strstr(plain, "Esc quit") != NULL);
	expect_true("footer has v0.2.4", strstr(plain, "v0.2.4") != NULL);
	expect_eq("footer visible width", (int)start_visible_len(plain), 80);

	/* Width sweep for the in-process cached version (env set above). */
	for (j = 0; j < sizeof(widths) / sizeof(widths[0]); j++)
		check_footer_version("0.2.4", widths[j]);
}

static void test_compose(void)
{
	start_menu_t menu;
	char *lines[24];
	size_t i;
	char joined[8192];
	size_t o = 0;

	setenv("NO_COLOR", "1", 1);
	expect_eq("load", start_menu_load_string(&menu, sample_menu), 0);
	start_compose_frame(lines, 24, 80, menu.rows, menu.row_count, 0);
	joined[0] = '\0';
	for (i = 0; i < 24; i++) {
		size_t n = strlen(lines[i]);
		if (o + n + 2 < sizeof(joined)) {
			memcpy(joined + o, lines[i], n);
			o += n;
			joined[o++] = '\n';
			joined[o] = '\0';
		}
		free(lines[i]);
	}
	expect_true("banner", strstr(joined, "Tamlinux Start") != NULL);
	expect_true("desktop label", strstr(joined, "Start graphical desktop shell") != NULL);
	expect_true("version footer", strstr(joined, "v") != NULL);
	expect_true("hints", strstr(joined, "Esc quit") != NULL);
	start_menu_free(&menu);
	unsetenv("NO_COLOR");
}

static void test_screen_diff(void)
{
	capture_t cap = {0};
	start_screen_t sc;
	char *f1[] = {"alpha", "bravo", "charlie"};
	char *f2[] = {"alpha", "BRAVO", "charlie"};
	int changed;

	start_screen_init(&sc, cap_write, cap_flush, &cap);
	start_screen_update(&sc, f1, 3, 10);
	expect_true("first paint cup", strstr(cap.blob, "\033[1;1H") != NULL);
	expect_true("no clear on update", strstr(cap.blob, "\033[2J") == NULL);
	expect_true("flushed", cap.flushes > 0);
	expect_true("short row still gets EL", strstr(cap.blob, "\033[K") != NULL);

	free(cap.blob);
	memset(&cap, 0, sizeof(cap));
	changed = start_screen_update(&sc, f2, 3, 10);
	expect_eq("one row changed", changed, 1);
	expect_true("middle cup", strstr(cap.blob, "\033[2;1H") != NULL);
	expect_true("no first cup", strstr(cap.blob, "\033[1;1H") == NULL);
	expect_true("no third cup", strstr(cap.blob, "\033[3;1H") == NULL);

	/* Full-width row must not be followed by EL (would erase last digit). */
	{
		char full10[] = "0123456789";
		char *f_full[] = {full10};
		char *at;

		free(cap.blob);
		memset(&cap, 0, sizeof(cap));
		start_screen_clear(&sc);
		start_screen_init(&sc, cap_write, cap_flush, &cap);
		start_screen_update(&sc, f_full, 1, 10);
		at = strstr(cap.blob, full10);
		expect_true("full row painted", at != NULL);
		expect_true("no EL after full-width row",
			    at && strncmp(at + 10, "\033[K", 3) != 0);
	}

	free(cap.blob);
	memset(&cap, 0, sizeof(cap));
	start_screen_enter(&sc);
	expect_true("alt screen", strstr(cap.blob, "\033[?1049h") != NULL);
	expect_true("disable wrap", strstr(cap.blob, "\033[?7l") != NULL);
	expect_true("clear on enter", strstr(cap.blob, "\033[2J") != NULL);
	free(cap.blob);
	cap.blob = NULL;
	cap.len = 0;
	{
		char *only[] = {"only"};
		start_screen_update(&sc, only, 1, 4);
		expect_true("no clear on later update", strstr(cap.blob ? cap.blob : "", "\033[2J") == NULL);
	}
	free(cap.blob);
	cap.blob = NULL;
	cap.len = 0;
	start_screen_leave(&sc);
	expect_true("restore wrap", strstr(cap.blob, "\033[?7h") != NULL);
	expect_true("leave alt", strstr(cap.blob, "\033[?1049l") != NULL);
	free(cap.blob);
	start_screen_clear(&sc);
}

static void test_packaged_menu_file(void)
{
	start_menu_t menu;
	const char *path = "menu.json";

	if (start_menu_load_file(&menu, path) != 0) {
		fprintf(stderr, "FAIL: load menu.json (run from commands/start)\n");
		failures++;
		return;
	}
	expect_eq("20 activities", (int)menu.count, 20);
	expect_streq("desktop first", menu.items[0].id, "desktop");
	expect_streq("desktop argv", menu.items[0].argv[0], "tam-desktop");
	expect_streq("guide second", menu.items[1].id, "tam-guide");
	expect_streq("guide argv", menu.items[1].argv[1], "show");
	expect_streq("glossary argv", menu.items[3].argv[2], "glossary");
	expect_eq("gnugo argc", menu.items[12].argc, 3);
	expect_streq("gnugo mode", menu.items[12].argv[1], "--mode");
	start_menu_free(&menu);
}

int main(void)
{
	printf("test_start\n");
	test_menu_parse();
	test_paginate();
	test_footer();
	test_compose();
	test_screen_diff();
	test_packaged_menu_file();
	if (failures) {
		fprintf(stderr, "%d failure(s)\n", failures);
		return 1;
	}
	printf("all passed\n");
	return 0;
}
