PREFIX ?= /usr/local

.PHONY: check install

check:
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 tam-shell-deploy $(DESTDIR)$(PREFIX)/bin/tam-shell-deploy
