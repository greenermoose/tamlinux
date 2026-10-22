PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-nut
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 tam-nut $(DESTDIR)$(PREFIX)/bin/tam-nut
