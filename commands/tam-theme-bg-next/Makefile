PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-bg-next
install:
	install -Dm755 tam-theme-bg-next $(DESTDIR)$(PREFIX)/bin/tam-theme-bg-next
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-bg-next/LICENSE
