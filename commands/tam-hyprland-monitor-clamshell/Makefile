PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-monitor-clamshell
install:
	install -Dm755 tam-hyprland-monitor-clamshell $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-clamshell
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-clamshell/LICENSE
