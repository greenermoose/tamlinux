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

#include <stdint.h>

enum tam_monitor_console_set {
    TAM_MONITOR_CONSOLE_SET_OK,
    TAM_MONITOR_CONSOLE_SET_OPEN,      /* cannot open /dev/fbN for writing */
    TAM_MONITOR_CONSOLE_SET_READ,      /* cannot read the screen settings */
    TAM_MONITOR_CONSOLE_SET_REFUSED,   /* the kernel refused the new area */
    TAM_MONITOR_CONSOLE_SET_UNVERIFIED /* applied, but readback differs */
};

/* Set the console area on fbN for every VT. *before_* receive the area that
 * was in effect, so a caller can put it back. *syserr is errno on failure. */
enum tam_monitor_console_set tam_monitor_console_set_area(unsigned fb, uint32_t width, uint32_t height,
    uint32_t *before_w, uint32_t *before_h, int *syserr);

/* Smallest width and height among the CRTCs lit on a DRM descriptor: the
 * area every lit monitor shows whole. False when none is lit. */
bool tam_monitor_console_lit_area(int drm_fd, uint32_t *width, uint32_t *height);

/* Whether this process may change the console area on fbN. */
bool tam_monitor_console_writable(unsigned fb);

/* Show or change the kernel console (fbcon) area on /dev/fbN. A change sets
 * only the visible size inside the framebuffer allocated at boot, for every
 * VT, until reboot; display modes are never changed. Returns an exit code. */
int tam_monitor_console_size(unsigned fb_index, enum tam_monitor_console_target target,
    const char *connector, unsigned width, unsigned height, bool json);

#endif
