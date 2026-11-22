PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-vt-screenshot
	python3 -B -m unittest discover -s tests -p 'test_*.py' -v
install:
	install -Dm755 tam-vt-screenshot $(DESTDIR)$(PREFIX)/bin/tam-vt-screenshot
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-vt-screenshot/LICENSE
