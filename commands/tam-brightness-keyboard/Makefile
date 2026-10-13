PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-brightness-keyboard
install:
	install -Dm755 tam-brightness-keyboard $(DESTDIR)$(PREFIX)/bin/tam-brightness-keyboard
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-brightness-keyboard/LICENSE
