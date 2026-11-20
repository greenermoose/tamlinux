PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-monitor-watch

install:
	install -Dm755 tam-hyprland-monitor-watch $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-watch
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-watch/LICENSE
