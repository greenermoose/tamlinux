PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-remove-security-fido2

install:
	install -Dm755 tam-remove-security-fido2 $(DESTDIR)$(PREFIX)/bin/tam-remove-security-fido2
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-remove-security-fido2/LICENSE
