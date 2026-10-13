PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-foot
install:
	install -Dm755 tam-theme-set-foot $(DESTDIR)$(PREFIX)/bin/tam-theme-set-foot
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-foot/LICENSE
