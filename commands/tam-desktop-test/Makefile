PREFIX ?= /usr/local

.PHONY: check install

check:
	python3 -B -m unittest discover -s ../../desktop/tests -p 'test_*.py' -v

install:
	install -Dm755 tam-desktop-test $(DESTDIR)$(PREFIX)/bin/tam-desktop-test
	install -Dm755 ../../desktop/test-battery $(DESTDIR)$(PREFIX)/share/tamlinux/desktop/test-battery
	install -Dm644 ../../desktop/virtual_input.py $(DESTDIR)$(PREFIX)/share/tamlinux/desktop/virtual_input.py
