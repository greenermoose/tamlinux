PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-default-editor

install:
	install -Dm755 tam-default-editor $(DESTDIR)$(PREFIX)/bin/tam-default-editor
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-default-editor/LICENSE
