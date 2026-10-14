PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-window-close-all

install:
	install -Dm755 tam-hyprland-window-close-all $(DESTDIR)$(PREFIX)/bin/tam-hyprland-window-close-all
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-window-close-all/LICENSE
