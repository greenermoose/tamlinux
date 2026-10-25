PREFIX ?= /usr/local
CC ?= cc
PKG_CONFIG ?= pkg-config
CFLAGS ?= -O2 -Wall -Wextra -Wpedantic
override CFLAGS += -g
LIBTAM_PREFIX ?=
DISPLAY_MIN_VERSION = 0.3.0
SESSION_CFLAGS = $(shell $(PKG_CONFIG) --cflags libsystemd)
SESSION_LIBS = $(shell $(PKG_CONFIG) --libs libsystemd)
ifneq ($(strip $(LIBTAM_PREFIX)),)
DISPLAY_CFLAGS = -I$(LIBTAM_PREFIX)/include
DISPLAY_ARCHIVE = $(LIBTAM_PREFIX)/lib/libtam-display.a
DISPLAY_LIBS = $(LIBTAM_PREFIX)/lib/libtam-display-session.a $(DISPLAY_ARCHIVE) $(SESSION_LIBS)
else
DISPLAY_CFLAGS = $(shell $(PKG_CONFIG) --cflags libtam-display 2>/dev/null)
DISPLAY_LIBS = $(shell $(PKG_CONFIG) --libs libtam-display-session 2>/dev/null)
DISPLAY_ARCHIVE = $(shell $(PKG_CONFIG) --variable=libdir libtam-display 2>/dev/null)/libtam-display.a
endif

.PHONY: check install native check-native display-api FORCE
native: build/tam-monitor

build:
	mkdir -p $@

display-api:
ifneq ($(strip $(LIBTAM_PREFIX)),)
	@test -f '$(LIBTAM_PREFIX)/include/tam_display.h' -a -f '$(DISPLAY_ARCHIVE)' -a -f '$(LIBTAM_PREFIX)/lib/libtam-display-session.a' -a -f '$(LIBTAM_PREFIX)/lib/pkgconfig/libtam-display-session.pc' || \
		{ echo 'Missing libtam-display development files under LIBTAM_PREFIX' >&2; exit 1; }
	@PKG_CONFIG_PATH='$(LIBTAM_PREFIX)/lib/pkgconfig:$(PKG_CONFIG_PATH)' $(PKG_CONFIG) --atleast-version=$(DISPLAY_MIN_VERSION) libtam-display-session || \
		{ echo 'Need libtam-display >= $(DISPLAY_MIN_VERSION), including its pkg-config metadata' >&2; exit 1; }
else
	@$(PKG_CONFIG) --atleast-version=$(DISPLAY_MIN_VERSION) libtam-display-session || \
		{ echo 'Need libtam-display >= $(DISPLAY_MIN_VERSION); set PKG_CONFIG_PATH or LIBTAM_PREFIX' >&2; exit 1; }
endif

build/.native-flags: FORCE | build
	@printf '%s\n' '$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) $(DISPLAY_LIBS)' > $@.tmp
	@cmp -s $@.tmp $@ && rm $@.tmp || mv $@.tmp $@

# API check runs first even when the development package is missing. The
# archive and generated header dependencies also invalidate existing clients.
NATIVE_SRCS = native.c native-preview.c native-events.c
NATIVE_OBJS = $(patsubst %.c,build/%.o,$(NATIVE_SRCS))
SESSION_ARCHIVE = $(dir $(DISPLAY_ARCHIVE))libtam-display-session.a
build/%.o: %.c build/.native-flags | display-api
	$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) -MMD -MP -c $< -o $@

build/tam-monitor: $(NATIVE_OBJS) $(wildcard $(DISPLAY_ARCHIVE) $(SESSION_ARCHIVE)) | display-api
	$(CC) $(CPPFLAGS) $(CFLAGS) $(NATIVE_OBJS) $(DISPLAY_LIBS) -o $@

-include $(NATIVE_OBJS:.o=.d)

check-native: native
	$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) $(NATIVE_SRCS) tests/native-fixture.c $(DISPLAY_LIBS) \
		-Wl,--wrap=tam_display_inspect_fd -o build/tam-monitor-fixture
	PYTHONDONTWRITEBYTECODE=1 python3 -B tests/native_cli.py

check:
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
install:
	install -Dm755 tam-monitor $(DESTDIR)$(PREFIX)/bin/tam-monitor
	install -Dm644 README.md $(DESTDIR)$(PREFIX)/share/doc/tam-monitor/README.md
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-monitor/LICENSE

PREVIEW_WRAPS = tam_monitor_hotplug_open tam_monitor_hotplug_event tam_vt_open tam_vt_check tam_vt_claim tam_vt_release tam_vt_close tam_display_session_open tam_display_session_device tam_display_session_bus_fd tam_display_session_bus_events tam_display_session_dispatch tam_display_session_check tam_display_session_check_restore tam_display_session_close tam_display_capture_fd tam_display_state_set_access_check tam_display_state_keep tam_display_state_restore tam_display_state_free
.PHONY: check-preview
check-preview: native
	$(CC) $(CPPFLAGS) $(CFLAGS) $(DISPLAY_CFLAGS) $(NATIVE_SRCS) tests/native-preview-fixture.c $(DISPLAY_LIBS) $(foreach s,$(PREVIEW_WRAPS),-Wl,--wrap=$(s)) -o build/tam-monitor-preview-fixture
	PYTHONDONTWRITEBYTECODE=1 python3 -B tests/native_preview.py

.PHONY: check-events
check-events: | build
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. tests/native_events.c native-events.c -o build/test-native-events
	./build/test-native-events
