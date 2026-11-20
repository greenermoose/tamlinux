PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-remove
install:
	install -Dm755 tam-theme-remove $(DESTDIR)$(PREFIX)/bin/tam-theme-remove
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-remove/LICENSE
