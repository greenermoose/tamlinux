PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-list
install:
	install -Dm755 tam-theme-list $(DESTDIR)$(PREFIX)/bin/tam-theme-list
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-list/LICENSE
