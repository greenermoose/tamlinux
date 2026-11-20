PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-terminal
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 tam-launch-terminal $(DESTDIR)$(PREFIX)/bin/tam-launch-terminal
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-terminal/LICENSE
