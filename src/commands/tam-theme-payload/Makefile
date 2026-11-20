PREFIX ?= /usr/local

.PHONY: check install

check:
	python3 -B -m unittest discover -s tests -t . -q

install:
	install -Dm755 tam-theme-payload $(DESTDIR)$(PREFIX)/bin/tam-theme-payload
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-payload/LICENSE
