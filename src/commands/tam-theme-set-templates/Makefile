PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-templates
install:
	install -Dm755 tam-theme-set-templates $(DESTDIR)$(PREFIX)/bin/tam-theme-set-templates
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-templates/LICENSE
