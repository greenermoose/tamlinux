PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-drive-password

install:
	install -Dm755 tam-drive-password $(DESTDIR)$(PREFIX)/bin/tam-drive-password
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-drive-password/LICENSE
