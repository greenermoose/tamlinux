PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-system-lock
install:
	install -Dm755 tam-system-lock $(DESTDIR)$(PREFIX)/bin/tam-system-lock
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-system-lock/LICENSE
	mkdir -p $(DESTDIR)$(PREFIX)/share/tamlinux/lock
	cp -R ../../desktop/lock/. $(DESTDIR)$(PREFIX)/share/tamlinux/lock/
