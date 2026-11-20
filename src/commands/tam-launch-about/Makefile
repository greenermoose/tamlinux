PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-launch-about
install:
	install -Dm755 tam-launch-about $(DESTDIR)$(PREFIX)/bin/tam-launch-about
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-launch-about/LICENSE
