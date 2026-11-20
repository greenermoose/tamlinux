PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-agent-crash

install:
	install -Dm755 tam-agent-crash $(DESTDIR)$(PREFIX)/bin/tam-agent-crash
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-agent-crash/LICENSE
