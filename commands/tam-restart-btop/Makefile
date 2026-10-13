PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-restart-btop
install:
	install -Dm755 tam-restart-btop $(DESTDIR)$(PREFIX)/bin/tam-restart-btop
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-btop/LICENSE
