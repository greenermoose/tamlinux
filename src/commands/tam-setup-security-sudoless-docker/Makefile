PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-setup-security-sudoless-docker

install:
	install -Dm755 tam-setup-security-sudoless-docker $(DESTDIR)$(PREFIX)/bin/tam-setup-security-sudoless-docker
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-setup-security-sudoless-docker/LICENSE
