PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-font-list
install:
	install -Dm755 tam-font-list $(DESTDIR)$(PREFIX)/bin/tam-font-list
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-font-list/LICENSE
