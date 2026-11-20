PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-toggle-enabled
install:
	install -Dm755 tam-toggle-enabled $(DESTDIR)$(PREFIX)/bin/tam-toggle-enabled
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-enabled/LICENSE
