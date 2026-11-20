PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-keyboard-f16
install:
	install -Dm755 tam-theme-set-keyboard-f16 $(DESTDIR)$(PREFIX)/bin/tam-theme-set-keyboard-f16
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-keyboard-f16/LICENSE
