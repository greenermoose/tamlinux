PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-tui-remove

install:
	install -Dm755 tam-tui-remove $(DESTDIR)$(PREFIX)/bin/tam-tui-remove
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-tui-remove/LICENSE
