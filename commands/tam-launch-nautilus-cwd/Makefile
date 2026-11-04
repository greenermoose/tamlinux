PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-nautilus-cwd

install:
	install -Dm755 tam-launch-nautilus-cwd $(DESTDIR)$(PREFIX)/bin/tam-launch-nautilus-cwd
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-nautilus-cwd/LICENSE
