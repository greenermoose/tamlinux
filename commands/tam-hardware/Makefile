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

CPUID_CFLAGS = $(shell $(PKG_CONFIG) --cflags libcpuid)
CPUID_LIBS = $(shell $(PKG_CONFIG) --libs libcpuid)

SRCS = tam-hardware.c probe.c format.c
OBJS = $(patsubst %.c,build/%.o,$(SRCS))

.PHONY: all check install clean

all: build/tam-hardware

build:
	mkdir -p $@

build/%.o: %.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) $(CPUID_CFLAGS) -I. -MMD -MP -c $< -o $@

build/tam-hardware: $(OBJS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OBJS) $(LIBTAM_LIBS) $(CPUID_LIBS) -o $@

-include $(OBJS:.o=.d)

build/test_probe: tests/test_probe.c probe.c format.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) $(CPUID_CFLAGS) -I. \
		tests/test_probe.c probe.c format.c $(LIBTAM_LIBS) $(CPUID_LIBS) -o $@

check: build/tam-hardware build/test_probe
	./build/test_probe
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_cli.py' -v

install: build/tam-hardware
	install -Dm755 build/tam-hardware $(DESTDIR)$(PREFIX)/bin/tam-hardware
	install -Dm644 README $(DESTDIR)$(PREFIX)/share/doc/tam-hardware/README
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hardware/LICENSE

clean:
	rm -rf build
