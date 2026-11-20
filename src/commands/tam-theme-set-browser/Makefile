PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-browser
	python3 -B -m unittest discover -s tests -q
install:
	install -Dm644 refresh.py $(DESTDIR)$(PREFIX)/share/tamlinux/browser-refresh.py
	install -Dm755 tam-theme-set-browser $(DESTDIR)$(PREFIX)/bin/tam-theme-set-browser
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-browser/LICENSE
