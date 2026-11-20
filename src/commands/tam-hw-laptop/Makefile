PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hw-laptop

install:
	install -Dm755 tam-hw-laptop $(DESTDIR)$(PREFIX)/bin/tam-hw-laptop
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-laptop/LICENSE
