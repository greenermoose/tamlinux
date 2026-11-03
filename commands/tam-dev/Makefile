PREFIX ?= /usr/local
.PHONY: check install
check:
	python3 -B -m unittest discover -s tests -q
install:
	install -Dm755 tam-dev $(DESTDIR)$(PREFIX)/bin/tam-dev
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-dev/LICENSE
