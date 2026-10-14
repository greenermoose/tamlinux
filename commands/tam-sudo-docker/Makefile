PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-sudo-docker

install:
	install -Dm755 tam-sudo-docker $(DESTDIR)$(PREFIX)/bin/tam-sudo-docker
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-sudo-docker/LICENSE
