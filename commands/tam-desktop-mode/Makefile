PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-desktop-mode
install:
	install -Dm755 tam-desktop-mode $(DESTDIR)$(PREFIX)/bin/tam-desktop-mode
	install -Dm755 ../../desktop/plugins/fred.workspaces/tam-desktop-mode $(DESTDIR)$(PREFIX)/share/tamlinux/workspaces/tam-desktop-mode
	install -Dm644 ../../desktop/shell/host/hyprland_backend.py $(DESTDIR)$(PREFIX)/share/tamlinux/workspaces/hyprland_backend.py
	install -Dm644 ../../desktop/shell/host/compositor_commands.py $(DESTDIR)$(PREFIX)/share/tamlinux/workspaces/compositor_commands.py
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-desktop-mode/LICENSE
