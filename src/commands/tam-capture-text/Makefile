PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-text
install:
	install -Dm755 tam-capture-text $(DESTDIR)$(PREFIX)/bin/tam-capture-text
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-text/LICENSE
