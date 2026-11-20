PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-select

install:
	install -Dm755 tam-menu-select $(DESTDIR)$(PREFIX)/bin/tam-menu-select
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-select/LICENSE
