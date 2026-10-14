PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-webapp-remove

install:
	install -Dm755 tam-webapp-remove $(DESTDIR)$(PREFIX)/bin/tam-webapp-remove
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-webapp-remove/LICENSE
