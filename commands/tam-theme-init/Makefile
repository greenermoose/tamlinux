PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-theme-init

install:
	install -Dm755 tam-theme-init $(DESTDIR)$(PREFIX)/bin/tam-theme-init
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-init/LICENSE
