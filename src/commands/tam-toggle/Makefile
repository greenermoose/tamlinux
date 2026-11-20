PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-toggle
install:
	install -Dm755 tam-toggle $(DESTDIR)$(PREFIX)/bin/tam-toggle
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle/LICENSE
