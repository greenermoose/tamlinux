PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-branding-screensaver
install:
	install -Dm755 tam-branding-screensaver $(DESTDIR)$(PREFIX)/bin/tam-branding-screensaver
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-branding-screensaver/LICENSE
