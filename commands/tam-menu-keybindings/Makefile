PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-keybindings

install:
	install -Dm755 tam-menu-keybindings $(DESTDIR)$(PREFIX)/bin/tam-menu-keybindings
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-keybindings/LICENSE
