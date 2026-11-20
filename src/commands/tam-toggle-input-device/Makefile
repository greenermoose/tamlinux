PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-toggle-input-device

install:
	install -Dm755 tam-toggle-input-device $(DESTDIR)$(PREFIX)/bin/tam-toggle-input-device
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-input-device/LICENSE
