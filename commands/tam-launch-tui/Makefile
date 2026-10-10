PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-tui

install:
	install -Dm755 tam-launch-tui $(DESTDIR)$(PREFIX)/bin/tam-launch-tui
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-tui/LICENSE
