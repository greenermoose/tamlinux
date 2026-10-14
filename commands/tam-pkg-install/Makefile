PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-pkg-install

install:
	install -Dm755 tam-pkg-install $(DESTDIR)$(PREFIX)/bin/tam-pkg-install
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-install/LICENSE
