PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-bg-switcher
install:
	install -Dm755 tam-theme-bg-switcher $(DESTDIR)$(PREFIX)/bin/tam-theme-bg-switcher
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-bg-switcher/LICENSE
