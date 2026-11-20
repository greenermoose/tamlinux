PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-menu-images
install:
	install -Dm755 tam-menu-images $(DESTDIR)$(PREFIX)/bin/tam-menu-images
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-images/LICENSE
