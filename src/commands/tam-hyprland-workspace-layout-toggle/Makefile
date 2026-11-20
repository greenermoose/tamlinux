PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-workspace-layout-toggle

install:
	install -Dm755 tam-hyprland-workspace-layout-toggle $(DESTDIR)$(PREFIX)/bin/tam-hyprland-workspace-layout-toggle
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-workspace-layout-toggle/LICENSE
