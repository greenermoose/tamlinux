#ifndef START_RUN_H
#define START_RUN_H

#include "menu.h"

/* Leave TUI before calling. Returns process exit status (or 1 on failure). */
int start_run_activity(const start_activity_t *item);

#endif /* START_RUN_H */
