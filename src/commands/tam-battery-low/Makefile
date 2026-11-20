PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-battery-low

install:
	install -Dm755 tam-battery-low $(DESTDIR)$(PREFIX)/bin/tam-battery-low
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-battery-low/LICENSE
