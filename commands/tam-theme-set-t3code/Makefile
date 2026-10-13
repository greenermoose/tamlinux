PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-t3code
install:
	install -Dm755 tam-theme-set-t3code $(DESTDIR)$(PREFIX)/bin/tam-theme-set-t3code
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-t3code/LICENSE
