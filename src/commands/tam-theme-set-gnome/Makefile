PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-gnome
install:
	install -Dm755 tam-theme-set-gnome $(DESTDIR)$(PREFIX)/bin/tam-theme-set-gnome
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-gnome/LICENSE
