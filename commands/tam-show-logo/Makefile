PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-show-logo

install:
	install -Dm755 tam-show-logo $(DESTDIR)$(PREFIX)/bin/tam-show-logo
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-show-logo/LICENSE
