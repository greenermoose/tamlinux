PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-setup-security-fido2

install:
	install -Dm755 tam-setup-security-fido2 $(DESTDIR)$(PREFIX)/bin/tam-setup-security-fido2
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-setup-security-fido2/LICENSE
