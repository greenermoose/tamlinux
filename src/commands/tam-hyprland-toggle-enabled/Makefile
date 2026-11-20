PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-toggle-enabled
install:
	install -Dm755 tam-hyprland-toggle-enabled $(DESTDIR)$(PREFIX)/bin/tam-hyprland-toggle-enabled
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-toggle-enabled/LICENSE
