PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-notification-wait

install:
	install -Dm755 tam-notification-wait $(DESTDIR)$(PREFIX)/bin/tam-notification-wait
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-notification-wait/LICENSE
