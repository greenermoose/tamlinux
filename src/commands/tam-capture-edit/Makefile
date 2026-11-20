PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-capture-edit
install:
	install -Dm755 tam-capture-edit $(DESTDIR)$(PREFIX)/bin/tam-capture-edit
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-edit/LICENSE
