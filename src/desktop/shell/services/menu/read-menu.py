#!/usr/bin/env python3
"""Read one regular UTF-8 menu file, bounded before it reaches QML."""
import os
import stat
import sys

LIMIT = 262144


def read_menu(path):
    # Follow normal config/store links, but never block opening a FIFO.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
            raise ValueError("menu must be a regular file of at most 256 KiB")
        with os.fdopen(fd, "rb", closefd=False) as source:
            raw = source.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError("menu exceeds 256 KiB")
        return raw.decode("utf-8", errors="strict")
    finally:
        os.close(fd)


if __name__ == "__main__":
    try:
        sys.stdout.write(read_menu(sys.argv[1]))
    except FileNotFoundError:
        sys.exit(3)
    except (OSError, ValueError, IndexError):
        sys.exit(2)
