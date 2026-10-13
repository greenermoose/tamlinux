PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-keyboard
install:
	install -Dm755 tam-theme-set-keyboard $(DESTDIR)$(PREFIX)/bin/tam-theme-set-keyboard
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-keyboard/LICENSE
