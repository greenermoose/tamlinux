PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-browser

install:
	install -Dm755 tam-launch-browser $(DESTDIR)$(PREFIX)/bin/tam-launch-browser
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-browser/LICENSE
