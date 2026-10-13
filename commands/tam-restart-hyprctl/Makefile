PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-restart-hyprctl
install:
	install -Dm755 tam-restart-hyprctl $(DESTDIR)$(PREFIX)/bin/tam-restart-hyprctl
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-hyprctl/LICENSE
