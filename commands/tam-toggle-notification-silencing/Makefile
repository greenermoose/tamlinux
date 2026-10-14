PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-toggle-notification-silencing

install:
	install -Dm755 tam-toggle-notification-silencing $(DESTDIR)$(PREFIX)/bin/tam-toggle-notification-silencing
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-notification-silencing/LICENSE
