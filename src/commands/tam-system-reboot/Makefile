PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-system-reboot

install:
	install -Dm755 tam-system-reboot $(DESTDIR)$(PREFIX)/bin/tam-system-reboot
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-reboot/LICENSE
