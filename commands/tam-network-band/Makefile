PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-network-band
install:
	install -Dm755 tam-network-band $(DESTDIR)$(PREFIX)/bin/tam-network-band
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-network-band/LICENSE
