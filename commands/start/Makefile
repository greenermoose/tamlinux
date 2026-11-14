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

SRCS = src/main.c src/menu.c src/util.c src/screen.c src/input.c src/frame.c src/run.c
OBJS = $(patsubst src/%.c,build/%.o,$(SRCS))

.PHONY: all check install uninstall clean

all: build/start

build:
	mkdir -p $@

build/%.o: src/%.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) -Isrc -MMD -MP -c $< -o $@

build/start: $(OBJS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OBJS) $(LIBTAM_LIBS) -o $@

-include $(OBJS:.o=.d)

build/test_start: tests/test_start.c src/menu.c src/util.c src/screen.c src/frame.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) -Isrc \
		tests/test_start.c src/menu.c src/util.c src/screen.c src/frame.c \
		$(LIBTAM_LIBS) -o $@

check: build/start build/test_start
	./build/test_start
	python3 -B tests/test_bundle_activation.py
	@START_MENU="$(CURDIR)/menu.json" START_VERSION=$$(cat VERSION) \
		./build/start --version | grep -E '^start [0-9]+\.[0-9]+\.[0-9]+$$'
	@START_MENU="$(CURDIR)/menu.json" ./build/start --list | head -n 3 | grep -E '^a +desktop'
	@START_MENU="$(CURDIR)/menu.json" ./build/start --check | grep -E 'activities installed'
	@START_MENU="$(CURDIR)/menu.json" ./build/start --help | grep -qi workstation
	@# Full patch versions must survive (regression: terminal wrap ate the last digit).
	@START_VERSION=0.3.0 START_MENU="$(CURDIR)/menu.json" ./build/start --check | grep -Eq 'v0\.3\.0$$'
	@START_VERSION=0.2.0 START_MENU="$(CURDIR)/menu.json" ./build/start --check | grep -Eq 'v0\.2\.0$$'
	@START_VERSION=0.2.4 START_MENU="$(CURDIR)/menu.json" ./build/start --check | grep -Eq 'v0\.2\.4$$'

install: build/start
	install -Dm755 build/start $(DESTDIR)$(PREFIX)/bin/start
	install -Dm644 menu.json $(DESTDIR)$(PREFIX)/share/start/menu.json
	install -Dm644 VERSION $(DESTDIR)$(PREFIX)/share/start/VERSION
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/start/LICENSE
	install -Dm644 README $(DESTDIR)$(PREFIX)/share/doc/start/README

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/start
	rm -f $(DESTDIR)$(PREFIX)/share/start/menu.json
	rm -f $(DESTDIR)$(PREFIX)/share/start/VERSION
	rm -f $(DESTDIR)$(PREFIX)/share/licenses/start/LICENSE
	rm -f $(DESTDIR)$(PREFIX)/share/doc/start/README

clean:
	rm -rf build
