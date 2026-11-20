PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-sudo-keepalive

install:
	install -Dm755 tam-sudo-keepalive $(DESTDIR)$(PREFIX)/bin/tam-sudo-keepalive
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-sudo-keepalive/LICENSE
