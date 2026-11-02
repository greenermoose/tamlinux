PREFIX ?= /usr/local

.PHONY: check install

check:
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 hi $(DESTDIR)$(PREFIX)/bin/hi
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/hi/LICENSE
