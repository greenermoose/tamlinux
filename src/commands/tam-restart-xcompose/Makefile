PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-restart-xcompose

install:
	install -Dm755 tam-restart-xcompose $(DESTDIR)$(PREFIX)/bin/tam-restart-xcompose
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-xcompose/LICENSE
