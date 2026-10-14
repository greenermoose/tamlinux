PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-pkg-remove

install:
	install -Dm755 tam-pkg-remove $(DESTDIR)$(PREFIX)/bin/tam-pkg-remove
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-remove/LICENSE
