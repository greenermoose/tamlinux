PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-toggle-nightlight
install:
	install -Dm755 tam-toggle-nightlight $(DESTDIR)$(PREFIX)/bin/tam-toggle-nightlight
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-nightlight/LICENSE
