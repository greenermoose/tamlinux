PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-brightness-keyboard-mute
install:
	install -Dm755 tam-brightness-keyboard-mute $(DESTDIR)$(PREFIX)/bin/tam-brightness-keyboard-mute
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-brightness-keyboard-mute/LICENSE
