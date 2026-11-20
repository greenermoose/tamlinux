PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hw-touchscreen

install:
	install -Dm755 tam-hw-touchscreen $(DESTDIR)$(PREFIX)/bin/tam-hw-touchscreen
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-touchscreen/LICENSE
