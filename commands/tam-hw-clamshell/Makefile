PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hw-clamshell
install:
	install -Dm755 tam-hw-clamshell $(DESTDIR)$(PREFIX)/bin/tam-hw-clamshell
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-clamshell/LICENSE
