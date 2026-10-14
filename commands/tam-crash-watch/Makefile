PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-crash-watch

install:
	install -Dm755 tam-crash-watch $(DESTDIR)$(PREFIX)/bin/tam-crash-watch
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-crash-watch/LICENSE
