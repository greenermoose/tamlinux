PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-monitor-internal-mirror
install:
	install -Dm755 tam-hyprland-monitor-internal-mirror $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-internal-mirror
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-internal-mirror/LICENSE
