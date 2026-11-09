#ifndef TAM_MONITOR_NATIVE_CONSOLE_H
#define TAM_MONITOR_NATIVE_CONSOLE_H

#include <stdbool.h>
#include <linux/fb.h>

/* Wrap points (defined in native.c so test fixtures can replace them). */
const char *tam_monitor_sysfs_graphics_path(void);
const char *tam_monitor_dev_path(void);
int tam_monitor_fb_get_var(int fd, struct fb_var_screeninfo *var);
int tam_monitor_fb_put_var(int fd, struct fb_var_screeninfo *var);

enum tam_monitor_console_target {
    TAM_MONITOR_CONSOLE_SHOW,    /* report only */
    TAM_MONITOR_CONSOLE_PIXELS,  /* explicit WIDTHxHEIGHT */
    TAM_MONITOR_CONSOLE_MONITOR, /* one lit monitor's current mode */
    TAM_MONITOR_CONSOLE_ALL      /* area every lit monitor shows whole */
};

/* Show or change the kernel console (fbcon) area on /dev/fbN. A change sets
 * only the visible size inside the framebuffer allocated at boot, for every
 * VT, until reboot; display modes are never changed. Returns an exit code. */
int tam_monitor_console_size(unsigned fb_index, enum tam_monitor_console_target target,
    const char *connector, unsigned width, unsigned height, bool json);

#endif
