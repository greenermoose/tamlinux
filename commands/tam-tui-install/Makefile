PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-tui-install

install:
	install -Dm755 tam-tui-install $(DESTDIR)$(PREFIX)/bin/tam-tui-install
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-tui-install/LICENSE
