PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-display-text-size
install:
	install -Dm755 tam-display-text-size $(DESTDIR)$(PREFIX)/bin/tam-display-text-size
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-display-text-size/LICENSE
