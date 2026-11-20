PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-disk-speedtest

install:
	install -Dm755 tam-disk-speedtest $(DESTDIR)$(PREFIX)/bin/tam-disk-speedtest
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-disk-speedtest/LICENSE
