PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-osd
install:
	install -Dm755 tam-osd $(DESTDIR)$(PREFIX)/bin/tam-osd
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-osd/LICENSE
