PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-network-password
install:
	install -Dm755 tam-network-password $(DESTDIR)$(PREFIX)/bin/tam-network-password
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-network-password/LICENSE
