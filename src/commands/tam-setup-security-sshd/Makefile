PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-setup-security-sshd

install:
	install -Dm755 tam-setup-security-sshd $(DESTDIR)$(PREFIX)/bin/tam-setup-security-sshd
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-setup-security-sshd/LICENSE
