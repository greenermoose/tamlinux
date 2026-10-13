PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-brightness-display-ddc
install:
	install -Dm755 tam-brightness-display-ddc $(DESTDIR)$(PREFIX)/bin/tam-brightness-display-ddc
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-brightness-display-ddc/LICENSE
