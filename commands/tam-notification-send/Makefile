PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-notification-send
	python3 -B -m unittest discover -s tests -q

install:
	install -Dm755 tam-notification-send $(DESTDIR)$(PREFIX)/bin/tam-notification-send
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-notification-send/LICENSE
