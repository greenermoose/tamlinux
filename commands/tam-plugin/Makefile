PREFIX ?= /usr/local

.PHONY: check install

check:
	bash tests/test-lifecycle-seams.sh

install:
	install -Dm755 tam-plugin $(DESTDIR)$(PREFIX)/bin/tam-plugin
