#ifndef START_SCREEN_H
#define START_SCREEN_H

#include <stddef.h>

typedef struct {
	char **rows;
	size_t height;
	int width;
	int entered;
	void (*write_fn)(const char *s, void *user);
	void (*flush_fn)(void *user);
	void *user;
} start_screen_t;

/* height is number of painted rows; width is terminal columns. */

void start_screen_init(start_screen_t *sc,
		       void (*write_fn)(const char *s, void *user),
		       void (*flush_fn)(void *user),
		       void *user);
void start_screen_enter(start_screen_t *sc);
void start_screen_leave(start_screen_t *sc);
/* Paint rows[0..height). Returns number of changed rows written. */
int start_screen_update(start_screen_t *sc, char **rows, size_t height, int width);
void start_screen_clear(start_screen_t *sc);

#endif /* START_SCREEN_H */
