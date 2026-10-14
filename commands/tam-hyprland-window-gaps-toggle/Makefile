PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-window-gaps-toggle

install:
	install -Dm755 tam-hyprland-window-gaps-toggle $(DESTDIR)$(PREFIX)/bin/tam-hyprland-window-gaps-toggle
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-window-gaps-toggle/LICENSE
