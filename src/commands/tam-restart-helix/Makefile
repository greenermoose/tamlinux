PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-restart-helix
install:
	install -Dm755 tam-restart-helix $(DESTDIR)$(PREFIX)/bin/tam-restart-helix
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-helix/LICENSE
