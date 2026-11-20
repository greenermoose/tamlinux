PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-toggle
install:
	install -Dm755 tam-hyprland-toggle $(DESTDIR)$(PREFIX)/bin/tam-hyprland-toggle
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-toggle/LICENSE
