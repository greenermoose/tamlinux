PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-restart-wifi
install:
	install -Dm755 tam-restart-wifi $(DESTDIR)$(PREFIX)/bin/tam-restart-wifi
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-wifi/LICENSE
