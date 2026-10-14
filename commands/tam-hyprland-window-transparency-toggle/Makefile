PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-window-transparency-toggle

install:
	install -Dm755 tam-hyprland-window-transparency-toggle $(DESTDIR)$(PREFIX)/bin/tam-hyprland-window-transparency-toggle
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-window-transparency-toggle/LICENSE
