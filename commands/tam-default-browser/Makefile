PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-default-browser

install:
	install -Dm755 tam-default-browser $(DESTDIR)$(PREFIX)/bin/tam-default-browser
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-default-browser/LICENSE
