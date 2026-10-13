PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-monitor-internal
install:
	install -Dm755 tam-hyprland-monitor-internal $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-internal
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-internal/LICENSE
