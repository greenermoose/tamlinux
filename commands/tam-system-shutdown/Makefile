PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-system-shutdown

install:
	install -Dm755 tam-system-shutdown $(DESTDIR)$(PREFIX)/bin/tam-system-shutdown
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-shutdown/LICENSE
