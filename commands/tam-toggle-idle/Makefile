PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-toggle-idle
install:
	install -Dm755 tam-toggle-idle $(DESTDIR)$(PREFIX)/bin/tam-toggle-idle
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-idle/LICENSE
