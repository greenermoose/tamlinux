PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-or-focus-tui

install:
	install -Dm755 tam-launch-or-focus-tui $(DESTDIR)$(PREFIX)/bin/tam-launch-or-focus-tui
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-or-focus-tui/LICENSE
