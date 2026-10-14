PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hw-dell-xps-haptic-touchpad

install:
	install -Dm755 tam-hw-dell-xps-haptic-touchpad $(DESTDIR)$(PREFIX)/bin/tam-hw-dell-xps-haptic-touchpad
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-dell-xps-haptic-touchpad/LICENSE
