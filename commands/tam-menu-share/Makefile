PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-share

install:
	install -Dm755 tam-menu-share $(DESTDIR)$(PREFIX)/bin/tam-menu-share
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-share/LICENSE
