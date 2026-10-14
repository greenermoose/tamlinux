PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-reload-guard

install:
	install -Dm755 tam-hyprland-reload-guard $(DESTDIR)$(PREFIX)/bin/tam-hyprland-reload-guard
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-reload-guard/LICENSE
