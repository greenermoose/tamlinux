PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-font-current
install:
	install -Dm755 tam-font-current $(DESTDIR)$(PREFIX)/bin/tam-font-current
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-font-current/LICENSE
