#include "native-events.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    const char drm[] = "change@/devices/test\0SUBSYSTEM=drm\0HOTPLUG=1";
    const char other[] = "change@/devices/test\0SUBSYSTEM=input\0HOTPLUG=1";
    const char quiet[] = "change@/devices/test\0SUBSYSTEM=drm\0HOTPLUG=0";
    assert(tam_monitor_hotplug_message(drm, sizeof(drm)));
    assert(!tam_monitor_hotplug_message(other, sizeof(other)));
    assert(!tam_monitor_hotplug_message(quiet, sizeof(quiet)));
    assert(tam_monitor_hotplug_message(drm, sizeof(drm)-1));
    assert(!tam_monitor_hotplug_message("", 0));
    puts("Bounded kernel DRM hotplug message parsing passed");
}
