PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-pkg-add
install:
	install -Dm755 tam-pkg-add $(DESTDIR)$(PREFIX)/bin/tam-pkg-add
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-add/LICENSE
