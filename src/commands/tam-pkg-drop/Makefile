PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-pkg-drop

install:
	install -Dm755 tam-pkg-drop $(DESTDIR)$(PREFIX)/bin/tam-pkg-drop
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-drop/LICENSE
