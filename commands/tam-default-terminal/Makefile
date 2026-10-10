PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-default-terminal

install:
	install -Dm755 tam-default-terminal $(DESTDIR)$(PREFIX)/bin/tam-default-terminal
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-default-terminal/LICENSE
