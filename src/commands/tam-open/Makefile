PREFIX ?= /usr/local
CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic -std=c11
override CFLAGS += -g

MAGIC_CFLAGS = $(shell $(PKG_CONFIG) --cflags libmagic)
MAGIC_LIBS = $(shell $(PKG_CONFIG) --libs libmagic)

SRCS = tam-open.c
OBJS = $(patsubst %.c,build/%.o,$(SRCS))

.PHONY: all check install clean

all: build/tam-open

build:
	mkdir -p $@

build/%.o: %.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(MAGIC_CFLAGS) -I. -MMD -MP -c $< -o $@

build/tam-open: $(OBJS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OBJS) $(MAGIC_LIBS) -o $@

-include $(OBJS:.o=.d)

check: build/tam-open
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_cli.py' -v

install: build/tam-open
	install -Dm755 build/tam-open $(DESTDIR)$(PREFIX)/bin/tam-open
	install -Dm644 README $(DESTDIR)$(PREFIX)/share/doc/tam-open/README
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-open/LICENSE

clean:
	rm -rf build
