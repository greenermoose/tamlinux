PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-font-set
install:
	install -Dm755 tam-font-set $(DESTDIR)$(PREFIX)/bin/tam-font-set
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-font-set/LICENSE
