PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-pkg-present
install:
	install -Dm755 tam-pkg-present $(DESTDIR)$(PREFIX)/bin/tam-pkg-present
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-present/LICENSE
