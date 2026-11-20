PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hyprland-monitor-scaling

install:
	install -Dm755 tam-hyprland-monitor-scaling $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-scaling
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-scaling/LICENSE
