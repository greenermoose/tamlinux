PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-focus-app

install:
	install -Dm755 tam-hyprland-focus-app $(DESTDIR)$(PREFIX)/bin/tam-hyprland-focus-app
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-focus-app/LICENSE
