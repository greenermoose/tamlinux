PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-notification-battery

install:
	install -Dm755 tam-notification-battery $(DESTDIR)$(PREFIX)/bin/tam-notification-battery
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-notification-battery/LICENSE
