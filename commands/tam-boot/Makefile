PREFIX ?= /usr/local
CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic -std=c11
override CFLAGS += -g

LIBTAM_PREFIX ?= $(shell \
	if $(PKG_CONFIG) --exists libtam 2>/dev/null; then :; \
	elif test -f "$(HOME)/.local/dev/lib/pkgconfig/libtam.pc"; then printf '%s' "$(HOME)/.local/dev"; fi)

ifneq ($(strip $(LIBTAM_PREFIX)),)
LIBTAM_CFLAGS = -I$(LIBTAM_PREFIX)/include
LIBTAM_LIBS = -L$(LIBTAM_PREFIX)/lib -ltam
PKG_CONFIG_PATH := $(LIBTAM_PREFIX)/lib/pkgconfig:$(PKG_CONFIG_PATH)
export PKG_CONFIG_PATH
else
LIBTAM_CFLAGS = $(shell $(PKG_CONFIG) --cflags libtam)
LIBTAM_LIBS = $(shell $(PKG_CONFIG) --libs libtam)
endif

SRCS = tam-boot.c journal.c report.c
OBJS = $(patsubst %.c,build/%.o,$(SRCS))

.PHONY: all check install clean

all: build/tam-boot

build:
	mkdir -p $@

build/%.o: %.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) -I. -MMD -MP -c $< -o $@

build/tam-boot: $(OBJS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OBJS) $(LIBTAM_LIBS) -o $@

-include $(OBJS:.o=.d)

build/test_boot: tests/test_boot.c journal.c report.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) -I. \
		tests/test_boot.c journal.c report.c $(LIBTAM_LIBS) -o $@

check: build/tam-boot build/test_boot
	./build/test_boot
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_cli.py' -v

install: build/tam-boot
	install -Dm755 build/tam-boot $(DESTDIR)$(PREFIX)/bin/tam-boot
	install -Dm644 README.md $(DESTDIR)$(PREFIX)/share/doc/tam-boot/README.md
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-boot/LICENSE

clean:
	rm -rf build
