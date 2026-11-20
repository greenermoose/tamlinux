PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-default-agent
install:
	install -Dm755 tam-default-agent $(DESTDIR)$(PREFIX)/bin/tam-default-agent
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-default-agent/LICENSE
