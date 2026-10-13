PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hw-laptop-closed
install:
	install -Dm755 tam-hw-laptop-closed $(DESTDIR)$(PREFIX)/bin/tam-hw-laptop-closed
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-laptop-closed/LICENSE
