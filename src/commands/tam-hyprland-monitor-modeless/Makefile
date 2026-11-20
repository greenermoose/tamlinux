PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-monitor-modeless

install:
	install -Dm755 tam-hyprland-monitor-modeless $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-modeless
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-modeless/LICENSE
