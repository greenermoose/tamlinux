PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-browser
install:
	install -Dm755 tam-theme-set-browser $(DESTDIR)$(PREFIX)/bin/tam-theme-set-browser
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-browser/LICENSE
