PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-install-font
install:
	install -Dm755 tam-install-font $(DESTDIR)$(PREFIX)/bin/tam-install-font
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-install-font/LICENSE
