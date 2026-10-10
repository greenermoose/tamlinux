PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-agent

install:
	install -Dm755 tam-agent $(DESTDIR)$(PREFIX)/bin/tam-agent
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-agent/LICENSE
