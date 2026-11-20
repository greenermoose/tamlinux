PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-switcher
install:
	install -Dm755 tam-theme-switcher $(DESTDIR)$(PREFIX)/bin/tam-theme-switcher
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-switcher/LICENSE
