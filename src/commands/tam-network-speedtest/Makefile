PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-network-speedtest
install:
	install -Dm755 tam-network-speedtest $(DESTDIR)$(PREFIX)/bin/tam-network-speedtest
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-network-speedtest/LICENSE
