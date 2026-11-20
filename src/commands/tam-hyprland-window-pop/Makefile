PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-window-pop

install:
	install -Dm755 tam-hyprland-window-pop $(DESTDIR)$(PREFIX)/bin/tam-hyprland-window-pop
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-window-pop/LICENSE
