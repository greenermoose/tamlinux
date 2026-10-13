PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-bluetooth-device
install:
	install -Dm755 tam-bluetooth-device $(DESTDIR)$(PREFIX)/bin/tam-bluetooth-device
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-bluetooth-device/LICENSE
