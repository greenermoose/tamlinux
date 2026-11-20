PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-pkg-missing
install:
	install -Dm755 tam-pkg-missing $(DESTDIR)$(PREFIX)/bin/tam-pkg-missing
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-pkg-missing/LICENSE
