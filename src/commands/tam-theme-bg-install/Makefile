PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-bg-install
install:
	install -Dm755 tam-theme-bg-install $(DESTDIR)$(PREFIX)/bin/tam-theme-bg-install
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-bg-install/LICENSE
