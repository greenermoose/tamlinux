PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-cmd-terminal-cwd

install:
	install -Dm755 tam-cmd-terminal-cwd $(DESTDIR)$(PREFIX)/bin/tam-cmd-terminal-cwd
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-cmd-terminal-cwd/LICENSE
