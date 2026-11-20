PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-webapp-install

install:
	install -Dm755 tam-webapp-install $(DESTDIR)$(PREFIX)/bin/tam-webapp-install
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-webapp-install/LICENSE
