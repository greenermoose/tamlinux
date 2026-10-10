PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-timezone

install:
	install -Dm755 tam-menu-timezone $(DESTDIR)$(PREFIX)/bin/tam-menu-timezone
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-timezone/LICENSE
