PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-system-logout

install:
	install -Dm755 tam-system-logout $(DESTDIR)$(PREFIX)/bin/tam-system-logout
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-logout/LICENSE
