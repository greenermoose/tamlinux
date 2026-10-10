PREFIX ?= /usr/local

.PHONY: check install

check:
	bash tests/test-lifecycle-seams.sh
	python3 -B -m unittest discover -s tests -q

install:
	install -Dm755 tam-plugin $(DESTDIR)$(PREFIX)/bin/tam-plugin
