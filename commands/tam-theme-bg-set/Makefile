PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-bg-set
install:
	install -Dm755 tam-theme-bg-set $(DESTDIR)$(PREFIX)/bin/tam-theme-bg-set
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-bg-set/LICENSE
