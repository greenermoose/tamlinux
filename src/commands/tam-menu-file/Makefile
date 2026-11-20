PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-file

install:
	install -Dm755 tam-menu-file $(DESTDIR)$(PREFIX)/bin/tam-menu-file
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-file/LICENSE
