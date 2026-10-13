PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-network-status
install:
	install -Dm755 tam-network-status $(DESTDIR)$(PREFIX)/bin/tam-network-status
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-network-status/LICENSE
