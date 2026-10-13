PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-region
	python3 -B tests/test_capture.py
install:
	install -Dm755 tam-capture-region $(DESTDIR)$(PREFIX)/bin/tam-capture-region
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-region/LICENSE
