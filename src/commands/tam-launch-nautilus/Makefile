PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-launch-nautilus

install:
	install -Dm755 tam-launch-nautilus $(DESTDIR)$(PREFIX)/bin/tam-launch-nautilus
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-nautilus/LICENSE
