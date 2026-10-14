PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-herdr-keybindings

install:
	install -Dm755 tam-menu-herdr-keybindings $(DESTDIR)$(PREFIX)/bin/tam-menu-herdr-keybindings
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-herdr-keybindings/LICENSE
