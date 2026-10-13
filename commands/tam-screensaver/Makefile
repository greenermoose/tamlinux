PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-screensaver
install:
	install -Dm755 tam-screensaver $(DESTDIR)$(PREFIX)/bin/tam-screensaver
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-screensaver/LICENSE
