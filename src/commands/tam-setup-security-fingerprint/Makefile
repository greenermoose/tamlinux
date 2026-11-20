PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-setup-security-fingerprint

install:
	install -Dm755 tam-setup-security-fingerprint $(DESTDIR)$(PREFIX)/bin/tam-setup-security-fingerprint
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-setup-security-fingerprint/LICENSE
