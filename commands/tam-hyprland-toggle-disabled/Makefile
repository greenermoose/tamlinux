PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-toggle-disabled
install:
	install -Dm755 tam-hyprland-toggle-disabled $(DESTDIR)$(PREFIX)/bin/tam-hyprland-toggle-disabled
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-toggle-disabled/LICENSE
