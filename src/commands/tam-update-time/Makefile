PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-update-time

install:
	install -Dm755 tam-update-time $(DESTDIR)$(PREFIX)/bin/tam-update-time
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-update-time/LICENSE
