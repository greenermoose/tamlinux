PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-dns
install:
	install -Dm755 tam-dns $(DESTDIR)$(PREFIX)/bin/tam-dns
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-dns/LICENSE
