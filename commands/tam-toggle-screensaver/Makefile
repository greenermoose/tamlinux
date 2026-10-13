PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-toggle-screensaver
install:
	install -Dm755 tam-toggle-screensaver $(DESTDIR)$(PREFIX)/bin/tam-toggle-screensaver
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-screensaver/LICENSE
