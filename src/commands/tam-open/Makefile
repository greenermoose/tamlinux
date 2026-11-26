PREFIX ?= /usr/local
CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic -std=c17
override CFLAGS += -g
# libtam 0.15.0 and later set no feature macros; tam-open uses GNU and
# POSIX.1-2008 interfaces.
override CPPFLAGS += -D_GNU_SOURCE

# libtam (program lookup, launching, file URLs, UTF-8), linked statically.
LIBTAM_PREFIX ?= $(shell \
	if $(PKG_CONFIG) --exists libtam 2>/dev/null; then :; \
	elif test -f "$(HOME)/.local/lib/pkgconfig/libtam.pc"; then printf '%s' "$(HOME)/.local"; fi)

ifneq ($(strip $(LIBTAM_PREFIX)),)
LIBTAM_CFLAGS = -I$(LIBTAM_PREFIX)/include
LIBTAM_LIBS = -L$(LIBTAM_PREFIX)/lib -ltam
else
LIBTAM_CFLAGS = $(shell $(PKG_CONFIG) --cflags libtam)
LIBTAM_LIBS = $(shell $(PKG_CONFIG) --libs libtam)
endif

MAGIC_CFLAGS = $(shell $(PKG_CONFIG) --cflags libmagic)
MAGIC_LIBS = $(shell $(PKG_CONFIG) --libs libmagic)

SRCS = tam-open.c
OBJS = $(patsubst %.c,build/%.o,$(SRCS))

.PHONY: all check install clean

all: build/tam-open

build:
	mkdir -p $@

build/%.o: %.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) $(MAGIC_CFLAGS) -I. -MMD -MP -c $< -o $@

build/tam-open: $(OBJS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OBJS) $(LIBTAM_LIBS) $(MAGIC_LIBS) -o $@

-include $(OBJS:.o=.d)

check: build/tam-open
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_cli.py' -v

install: build/tam-open
	install -Dm755 build/tam-open $(DESTDIR)$(PREFIX)/bin/tam-open
	install -Dm644 README $(DESTDIR)$(PREFIX)/share/doc/tam-open/README
	install -Dm644 ../../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-open/LICENSE

clean:
	rm -rf build
