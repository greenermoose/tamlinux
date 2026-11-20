PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hw-display
install:
	install -Dm755 tam-hw-display $(DESTDIR)$(PREFIX)/bin/tam-hw-display
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-display/LICENSE
