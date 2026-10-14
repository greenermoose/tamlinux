PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-restart-trackpad

install:
	install -Dm755 tam-restart-trackpad $(DESTDIR)$(PREFIX)/bin/tam-restart-trackpad
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-trackpad/LICENSE
