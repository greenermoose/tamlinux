PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-editor

install:
	install -Dm755 tam-launch-editor $(DESTDIR)$(PREFIX)/bin/tam-launch-editor
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-editor/LICENSE
