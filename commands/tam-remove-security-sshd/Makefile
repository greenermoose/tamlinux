PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-remove-security-sshd

install:
	install -Dm755 tam-remove-security-sshd $(DESTDIR)$(PREFIX)/bin/tam-remove-security-sshd
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-remove-security-sshd/LICENSE
