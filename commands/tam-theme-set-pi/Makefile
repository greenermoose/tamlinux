PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-pi
install:
	install -Dm755 tam-theme-set-pi $(DESTDIR)$(PREFIX)/bin/tam-theme-set-pi
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-pi/LICENSE
