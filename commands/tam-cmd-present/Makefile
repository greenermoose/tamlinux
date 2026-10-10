PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-cmd-present

install:
	install -Dm755 tam-cmd-present $(DESTDIR)$(PREFIX)/bin/tam-cmd-present
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-cmd-present/LICENSE
