PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-journal
install:
	install -Dm755 tam-theme-journal $(DESTDIR)$(PREFIX)/bin/tam-theme-journal
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-journal/LICENSE
