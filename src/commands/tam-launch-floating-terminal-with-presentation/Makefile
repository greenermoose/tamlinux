PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-floating-terminal-with-presentation

install:
	install -Dm755 tam-launch-floating-terminal-with-presentation $(DESTDIR)$(PREFIX)/bin/tam-launch-floating-terminal-with-presentation
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-floating-terminal-with-presentation/LICENSE
