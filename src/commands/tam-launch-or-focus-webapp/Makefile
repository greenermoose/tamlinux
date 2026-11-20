PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-or-focus-webapp

install:
	install -Dm755 tam-launch-or-focus-webapp $(DESTDIR)$(PREFIX)/bin/tam-launch-or-focus-webapp
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-or-focus-webapp/LICENSE
