PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-current
install:
	install -Dm755 tam-theme-current $(DESTDIR)$(PREFIX)/bin/tam-theme-current
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-current/LICENSE
