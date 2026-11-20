PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-notification-time

install:
	install -Dm755 tam-notification-time $(DESTDIR)$(PREFIX)/bin/tam-notification-time
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-notification-time/LICENSE
