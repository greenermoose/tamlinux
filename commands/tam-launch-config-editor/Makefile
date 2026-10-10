PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-config-editor

install:
	install -Dm755 tam-launch-config-editor $(DESTDIR)$(PREFIX)/bin/tam-launch-config-editor
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-config-editor/LICENSE
