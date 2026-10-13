PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-system-wake
install:
	install -Dm755 tam-system-wake $(DESTDIR)$(PREFIX)/bin/tam-system-wake
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-wake/LICENSE
