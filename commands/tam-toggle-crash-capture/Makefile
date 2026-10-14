PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-toggle-crash-capture

install:
	install -Dm755 tam-toggle-crash-capture $(DESTDIR)$(PREFIX)/bin/tam-toggle-crash-capture
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-crash-capture/LICENSE
