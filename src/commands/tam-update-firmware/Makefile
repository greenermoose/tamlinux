PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-update-firmware
install:
	install -Dm755 tam-update-firmware $(DESTDIR)$(PREFIX)/bin/tam-update-firmware
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-update-firmware/LICENSE
