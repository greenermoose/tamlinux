PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-restart-bluetooth
install:
	install -Dm755 tam-restart-bluetooth $(DESTDIR)$(PREFIX)/bin/tam-restart-bluetooth
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-bluetooth/LICENSE
