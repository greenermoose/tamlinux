PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-webapp

install:
	install -Dm755 tam-launch-webapp $(DESTDIR)$(PREFIX)/bin/tam-launch-webapp
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-webapp/LICENSE
