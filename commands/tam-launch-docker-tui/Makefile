PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-docker-tui

install:
	install -Dm755 tam-launch-docker-tui $(DESTDIR)$(PREFIX)/bin/tam-launch-docker-tui
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-docker-tui/LICENSE
