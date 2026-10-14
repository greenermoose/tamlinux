PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-window-width

install:
	install -Dm755 tam-hyprland-window-width $(DESTDIR)$(PREFIX)/bin/tam-hyprland-window-width
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-window-width/LICENSE
