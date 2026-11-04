PREFIX ?= /usr/local

.PHONY: check install

check:
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 start $(DESTDIR)$(PREFIX)/bin/start
	install -Dm644 VERSION $(DESTDIR)$(PREFIX)/share/start/VERSION
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/start/LICENSE
