#ifndef START_UTIL_H
#define START_UTIL_H

#include <stddef.h>
#include <stdbool.h>

#define START_CHROME_TOP 7
#define START_CHROME_BOTTOM 1
#define START_MAX_ACTIVITIES 26
#define START_MAX_ARGV 8
#define START_FOOTER_HINTS \
	"Down/Up Arrow scroll  Home top  End bottom  Backspace quit"

bool start_use_color(void);
const char *start_version(void);
char *start_find_data_file(const char *name);
bool start_command_on_path(const char *cmd);
size_t start_visible_len(const char *text);
void start_strip_ansi(char *dst, size_t dstsz, const char *src);
void start_clip_pad(char *dst, size_t dstsz, const char *text, int width);
void start_terminal_size(int *cols, int *rows);
int start_page_capacity(int rows);

const char *start_sgr_bold(void);
const char *start_sgr_dim(void);
const char *start_sgr_cyan(void);
const char *start_sgr_green(void);
const char *start_sgr_yellow(void);
const char *start_sgr_reset(void);
const char *start_attention_on(void);
const char *start_attention_off(void);

#endif /* START_UTIL_H */
