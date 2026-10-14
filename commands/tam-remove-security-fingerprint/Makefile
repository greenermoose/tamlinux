PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-remove-security-fingerprint

install:
	install -Dm755 tam-remove-security-fingerprint $(DESTDIR)$(PREFIX)/bin/tam-remove-security-fingerprint
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-remove-security-fingerprint/LICENSE
