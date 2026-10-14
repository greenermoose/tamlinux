PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-remove-launcher-entry

install:
	install -Dm755 tam-remove-launcher-entry $(DESTDIR)$(PREFIX)/bin/tam-remove-launcher-entry
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-remove-launcher-entry/LICENSE
