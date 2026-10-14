PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-remove-security-sudoless-docker

install:
	install -Dm755 tam-remove-security-sudoless-docker $(DESTDIR)$(PREFIX)/bin/tam-remove-security-sudoless-docker
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-remove-security-sudoless-docker/LICENSE
