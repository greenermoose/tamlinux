PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hyprland-monitor-focused-apple
install:
	install -Dm755 tam-hyprland-monitor-focused-apple $(DESTDIR)$(PREFIX)/bin/tam-hyprland-monitor-focused-apple
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hyprland-monitor-focused-apple/LICENSE
