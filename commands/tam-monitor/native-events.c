#define _GNU_SOURCE
#include "native-events.h"
#include <errno.h>
#include <linux/netlink.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int tam_monitor_hotplug_open(void)
{
    int fd = socket(AF_NETLINK, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, NETLINK_KOBJECT_UEVENT);
    if (fd < 0) return -1;
    struct sockaddr_nl address = {.nl_family = AF_NETLINK, .nl_groups = 1};
    if (bind(fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        int saved = errno; close(fd); errno = saved; return -1;
    }
    return fd;
}

bool tam_monitor_hotplug_message(const char *message, size_t length)
{
    bool drm = false, hotplug = false;
    for (size_t i = 0; i < length;) {
        const char *end = memchr(message + i, 0, length - i);
        if (!end) return true; /* Truncation/loss requires conservative recovery. */
        size_t n = (size_t)(end - message - i);
        if (n == 13 && !memcmp(message + i, "SUBSYSTEM=drm", n)) drm = true;
        if (n == 9 && !memcmp(message + i, "HOTPLUG=1", n)) hotplug = true;
        i += n + 1;
    }
    return drm && hotplug;
}

bool tam_monitor_hotplug_event(int fd)
{
    /* Drain a bounded batch, preserving deadline/event fairness. */
    for (int i = 0; i < 32; ++i) {
        char message[8192];
        struct sockaddr_nl from = {0};
        struct iovec vector = {.iov_base = message, .iov_len = sizeof(message)};
        struct msghdr msg = {.msg_name = &from, .msg_namelen = sizeof(from), .msg_iov = &vector, .msg_iovlen = 1};
        ssize_t n = recvmsg(fd, &msg, MSG_DONTWAIT);
        if (n < 0) return errno != EAGAIN && errno != EWOULDBLOCK;
        if (from.nl_pid != 0 || from.nl_family != AF_NETLINK) continue;
        if ((msg.msg_flags & MSG_TRUNC) || n == 0 || tam_monitor_hotplug_message(message, (size_t)n)) return true;
    }
    return false;
}
