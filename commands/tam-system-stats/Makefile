PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-system-stats
install:
	install -Dm755 tam-system-stats $(DESTDIR)$(PREFIX)/bin/tam-system-stats
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-stats/LICENSE
