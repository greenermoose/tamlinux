PREFIX ?= /usr/local

.PHONY: check install

check:
	@if [ -z "$(TAM_CHECK_ALL)" ]; then \
		python3 -B -m unittest discover -s ../../../tests -p 'test_virtual_input.py' && \
		python3 -B -m unittest discover -s ../../../tests -p 'test_desktop_battery.py'; \
	fi

install:
	install -Dm755 tam-desktop-test $(DESTDIR)$(PREFIX)/bin/tam-desktop-test
	install -Dm755 ../../../tests/test-battery $(DESTDIR)$(PREFIX)/share/tamlinux/desktop/test-battery
	install -Dm644 ../../desktop/virtual_input.py $(DESTDIR)$(PREFIX)/share/tamlinux/desktop/virtual_input.py
