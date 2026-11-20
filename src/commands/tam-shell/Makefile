PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-shell
	python3 -B -m unittest discover -s tests -q

install:
	install -Dm755 tam-shell $(DESTDIR)$(PREFIX)/bin/tam-shell
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-shell/LICENSE
