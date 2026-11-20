PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-network-qr
install:
	install -Dm755 tam-network-qr $(DESTDIR)$(PREFIX)/bin/tam-network-qr
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-network-qr/LICENSE
