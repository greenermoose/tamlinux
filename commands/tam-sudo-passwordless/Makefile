PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-sudo-passwordless

install:
	install -Dm755 tam-sudo-passwordless $(DESTDIR)$(PREFIX)/bin/tam-sudo-passwordless
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-sudo-passwordless/LICENSE
