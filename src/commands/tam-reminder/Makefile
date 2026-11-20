PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-reminder

install:
	install -Dm755 tam-reminder $(DESTDIR)$(PREFIX)/bin/tam-reminder
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-reminder/LICENSE
