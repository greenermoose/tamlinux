#ifndef START_INPUT_H
#define START_INPUT_H

#include <stddef.h>

#define START_KEY_UP "up"
#define START_KEY_DOWN "down"
#define START_KEY_RIGHT "right"
#define START_KEY_ENTER "enter"
#define START_KEY_BACKSPACE "backspace"
#define START_KEY_DELETE "delete"
#define START_KEY_PGUP "pgup"
#define START_KEY_PGDN "pgdn"
#define START_KEY_HOME "home"
#define START_KEY_END "end"
#define START_KEY_SPACE "space"
#define START_KEY_BACKTICK "backtick"
#define START_KEY_ESC "esc"

/* Read one logical key from a tty fd in cbreak mode into buf (NUL-terminated).
 * Letter keys are lowercased single characters. Returns 0 on success, -1 on EOF. */
int start_read_key(int fd, char *buf, size_t bufsz);

#endif /* START_INPUT_H */
