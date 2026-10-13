PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-monitor-laptop
install:
	install -Dm755 tam-hyprland-monitor-laptop $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-laptop
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-laptop/LICENSE
