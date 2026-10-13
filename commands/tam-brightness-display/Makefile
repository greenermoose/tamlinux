PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-brightness-display
install:
	install -Dm755 tam-brightness-display $(DESTDIR)$(PREFIX)/bin/tam-brightness-display
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-brightness-display/LICENSE
