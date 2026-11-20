PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hw-fingerprint

install:
	install -Dm755 tam-hw-fingerprint $(DESTDIR)$(PREFIX)/bin/tam-hw-fingerprint
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-fingerprint/LICENSE
