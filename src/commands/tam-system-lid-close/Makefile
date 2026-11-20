PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-system-lid-close

install:
	install -Dm755 tam-system-lid-close $(DESTDIR)$(PREFIX)/bin/tam-system-lid-close
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-lid-close/LICENSE
