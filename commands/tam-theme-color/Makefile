PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-color
install:
	install -Dm755 tam-theme-color $(DESTDIR)$(PREFIX)/bin/tam-theme-color
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-color/LICENSE
