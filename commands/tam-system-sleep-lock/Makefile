PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-system-sleep-lock
install:
	install -Dm755 tam-system-sleep-lock $(DESTDIR)$(PREFIX)/bin/tam-system-sleep-lock
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-sleep-lock/LICENSE
