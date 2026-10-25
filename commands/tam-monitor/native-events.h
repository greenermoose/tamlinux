#ifndef TAM_MONITOR_EVENTS_H
#define TAM_MONITOR_EVENTS_H
#include <stdbool.h>
#include <stddef.h>
/* Listen to kernel hotplug notifications; no sysfs writes or periodic polls. */
int tam_monitor_hotplug_open(void);
bool tam_monitor_hotplug_event(int fd);
bool tam_monitor_hotplug_message(const char *message, size_t length);
#endif
