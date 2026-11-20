PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-branding-about
install:
	install -Dm755 tam-branding-about $(DESTDIR)$(PREFIX)/bin/tam-branding-about
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-branding-about/LICENSE
