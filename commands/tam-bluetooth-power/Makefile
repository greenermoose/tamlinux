PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-bluetooth-power
install:
	install -Dm755 tam-bluetooth-power $(DESTDIR)$(PREFIX)/bin/tam-bluetooth-power
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-bluetooth-power/LICENSE
