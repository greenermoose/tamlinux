PREFIX ?= /usr/local
CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic
override CFLAGS += -g
LIBTAM_PREFIX ?=
DISPLAY_MIN_VERSION = 0.1.0
ifneq ($(strip $(LIBTAM_PREFIX)),)
DISPLAY_CFLAGS = -I$(LIBTAM_PREFIX)/include
DISPLAY_ARCHIVE = $(LIBTAM_PREFIX)/lib/libtam-display.a
DISPLAY_LIBS = $(DISPLAY_ARCHIVE)
else
DISPLAY_CFLAGS = $(shell $(PKG_CONFIG) --cflags libtam-display 2>/dev/null)
DISPLAY_LIBS = $(shell $(PKG_CONFIG) --libs libtam-display 2>/dev/null)
DISPLAY_ARCHIVE = $(shell $(PKG_CONFIG) --variable=libdir libtam-display 2>/dev/null)/libtam-display.a
endif

.PHONY: check install native check-native display-api FORCE
native: build/tam-monitor

build:
	mkdir -p $@

display-api:
ifneq ($(strip $(LIBTAM_PREFIX)),)
	@test -f '$(LIBTAM_PREFIX)/include/tam_display.h' -a -f '$(DISPLAY_ARCHIVE)' || \
		{ echo 'Missing libtam-display development files under LIBTAM_PREFIX' >&2; exit 1; }
	@PKG_CONFIG_LIBDIR='$(LIBTAM_PREFIX)/lib/pkgconfig' $(PKG_CONFIG) --atleast-version=$(DISPLAY_MIN_VERSION) libtam-display || \
		{ echo 'Need libtam-display >= $(DISPLAY_MIN_VERSION), including its pkg-config metadata' >&2; exit 1; }
else
	@$(PKG_CONFIG) --atleast-version=$(DISPLAY_MIN_VERSION) libtam-display || \
		{ echo 'Need libtam-display >= $(DISPLAY_MIN_VERSION); set PKG_CONFIG_PATH or LIBTAM_PREFIX' >&2; exit 1; }
endif

build/.native-flags: FORCE | build
	@printf '%s\n' '$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) $(DISPLAY_LIBS)' > $@.tmp
	@cmp -s $@.tmp $@ && rm $@.tmp || mv $@.tmp $@

# API check runs first even when the development package is missing. The
# archive and generated header dependencies also invalidate existing clients.
build/tam-monitor: native.c build/.native-flags $(wildcard $(DISPLAY_ARCHIVE)) | display-api
	$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) -MMD -MP $< $(DISPLAY_LIBS) -o $@

-include build/tam-monitor.d

check-native: native
	$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) native.c tests/native-fixture.c $(DISPLAY_LIBS) \
		-Wl,--wrap=tam_display_inspect_fd -o build/tam-monitor-fixture
	PYTHONDONTWRITEBYTECODE=1 python3 -B tests/native_cli.py

check:
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
install:
	install -Dm755 tam-monitor $(DESTDIR)$(PREFIX)/bin/tam-monitor
	install -Dm644 README.md $(DESTDIR)$(PREFIX)/share/doc/tam-monitor/README.md
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-monitor/LICENSE
