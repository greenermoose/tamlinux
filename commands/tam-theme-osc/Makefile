PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-osc
install:
	install -Dm755 tam-theme-osc $(DESTDIR)$(PREFIX)/bin/tam-theme-osc
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-osc/LICENSE
