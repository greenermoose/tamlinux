PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hibernation-available

install:
	install -Dm755 tam-hibernation-available $(DESTDIR)$(PREFIX)/bin/tam-hibernation-available
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hibernation-available/LICENSE
