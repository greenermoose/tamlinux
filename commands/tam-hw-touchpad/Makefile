PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hw-touchpad

install:
	install -Dm755 tam-hw-touchpad $(DESTDIR)$(PREFIX)/bin/tam-hw-touchpad
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-touchpad/LICENSE
