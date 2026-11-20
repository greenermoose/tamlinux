PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-restart-shell

install:
	install -Dm755 tam-restart-shell $(DESTDIR)$(PREFIX)/bin/tam-restart-shell
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-shell/LICENSE
