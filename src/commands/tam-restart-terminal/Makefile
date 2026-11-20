PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-restart-terminal
install:
	install -Dm755 tam-restart-terminal $(DESTDIR)$(PREFIX)/bin/tam-restart-terminal
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-terminal/LICENSE
