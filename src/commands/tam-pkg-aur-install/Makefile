PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-pkg-aur-install

install:
	install -Dm755 tam-pkg-aur-install $(DESTDIR)$(PREFIX)/bin/tam-pkg-aur-install
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-aur-install/LICENSE
