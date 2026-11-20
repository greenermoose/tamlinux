PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-qr
install:
	install -Dm755 tam-capture-qr $(DESTDIR)$(PREFIX)/bin/tam-capture-qr
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-qr/LICENSE
