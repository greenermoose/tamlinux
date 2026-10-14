PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-migrate-desktop
install:
	install -Dm755 tam-migrate-desktop $(DESTDIR)$(PREFIX)/bin/tam-migrate-desktop
	install -Dm644 ../../desktop/migration/engine.py $(DESTDIR)$(PREFIX)/share/tamlinux/migration/engine.py
	install -Dm644 ../../desktop/migration/paths.json $(DESTDIR)$(PREFIX)/share/tamlinux/migration/paths.json
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-migrate-desktop/LICENSE
