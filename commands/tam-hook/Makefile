PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-hook
install:
	install -Dm755 tam-hook $(DESTDIR)$(PREFIX)/bin/tam-hook
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hook/LICENSE
