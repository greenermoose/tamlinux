PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-qmlcache-purge

install:
	install -Dm755 tam-qmlcache-purge $(DESTDIR)$(PREFIX)/bin/tam-qmlcache-purge
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-qmlcache-purge/LICENSE
