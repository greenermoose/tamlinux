PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hw-external-monitors
install:
	install -Dm755 tam-hw-external-monitors $(DESTDIR)$(PREFIX)/bin/tam-hw-external-monitors
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-external-monitors/LICENSE
