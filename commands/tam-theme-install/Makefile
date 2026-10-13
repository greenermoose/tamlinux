PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-install
install:
	install -Dm755 tam-theme-install $(DESTDIR)$(PREFIX)/bin/tam-theme-install
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-install/LICENSE
