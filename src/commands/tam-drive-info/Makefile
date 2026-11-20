PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-drive-info

install:
	install -Dm755 tam-drive-info $(DESTDIR)$(PREFIX)/bin/tam-drive-info
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-drive-info/LICENSE
