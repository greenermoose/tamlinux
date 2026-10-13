PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-launch-screensaver
install:
	install -Dm755 tam-launch-screensaver $(DESTDIR)$(PREFIX)/bin/tam-launch-screensaver
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-screensaver/LICENSE
	mkdir -p $(DESTDIR)$(PREFIX)/share/tamlinux/screensaver
	cp -R ../../desktop/screensaver/. $(DESTDIR)$(PREFIX)/share/tamlinux/screensaver/
