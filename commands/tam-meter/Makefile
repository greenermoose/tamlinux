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

SRCS = tam-meter.c sensors.c stats.c report.c live.c
OBJS = $(patsubst %.c,build/%.o,$(SRCS))

.PHONY: all check install clean

all: build/tam-meter

build:
	mkdir -p $@

build/%.o: %.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) -I. -MMD -MP -c $< -o $@

build/tam-meter: $(OBJS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OBJS) $(LIBTAM_LIBS) -lm -o $@

-include $(OBJS:.o=.d)

build/test_meter: tests/test_meter.c sensors.c stats.c report.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) -I. \
		tests/test_meter.c sensors.c stats.c report.c $(LIBTAM_LIBS) -lm -o $@

check: build/tam-meter build/test_meter
	./build/test_meter
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_cli.py' -v

install: build/tam-meter
	install -Dm755 build/tam-meter $(DESTDIR)$(PREFIX)/bin/tam-meter
	install -Dm644 README.md $(DESTDIR)$(PREFIX)/share/doc/tam-meter/README.md
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-meter/LICENSE

clean:
	rm -rf build
