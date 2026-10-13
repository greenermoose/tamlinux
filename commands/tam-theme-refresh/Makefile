PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-refresh
install:
	install -Dm755 tam-theme-refresh $(DESTDIR)$(PREFIX)/bin/tam-theme-refresh
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-refresh/LICENSE
