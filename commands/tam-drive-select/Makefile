PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-drive-select

install:
	install -Dm755 tam-drive-select $(DESTDIR)$(PREFIX)/bin/tam-drive-select
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-drive-select/LICENSE
