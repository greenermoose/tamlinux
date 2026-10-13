PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-battery-status
install:
	install -Dm755 tam-battery-status $(DESTDIR)$(PREFIX)/bin/tam-battery-status
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-battery-status/LICENSE
