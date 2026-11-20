PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-monitor-external-active
install:
	install -Dm755 tam-hyprland-monitor-external-active $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-external-active
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-external-active/LICENSE
