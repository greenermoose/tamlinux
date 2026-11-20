PREFIX ?= /usr/local

.PHONY: check install

check:
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 tam-browser-command $(DESTDIR)$(PREFIX)/bin/tam-browser-command
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-browser-command/LICENSE
