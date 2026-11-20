PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-session-init
install:
	install -Dm755 tam-session-init $(DESTDIR)$(PREFIX)/bin/tam-session-init
	install -Dm644 ../../desktop/session/initialize.py $(DESTDIR)$(PREFIX)/share/tamlinux/session/initialize.py
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-session-init/LICENSE
