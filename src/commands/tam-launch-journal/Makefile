PREFIX ?= /usr/local
CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -g -Wall -Wextra -Wpedantic -std=c11
ifdef LIBTAM_PREFIX
LIBTAM_CFLAGS = -I$(LIBTAM_PREFIX)/include
LIBTAM_LIBS = -L$(LIBTAM_PREFIX)/lib -ltam
else
LIBTAM_CFLAGS = $(shell $(PKG_CONFIG) --cflags libtam)
LIBTAM_LIBS = $(shell $(PKG_CONFIG) --libs libtam)
endif
.PHONY: all check install clean
all: build/tam-launch-journal
build/tam-launch-journal: tam-launch-journal.c
	mkdir -p build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LIBTAM_CFLAGS) $< $(LIBTAM_LIBS) -o $@
check: all
	./build/tam-launch-journal invalid; test $$? -eq 2
install: all
	install -Dm755 build/tam-launch-journal $(DESTDIR)$(PREFIX)/bin/tam-launch-journal
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-journal/LICENSE
clean:
	rm -f build/tam-launch-journal
