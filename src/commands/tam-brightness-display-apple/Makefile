PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-brightness-display-apple
install:
	install -Dm755 tam-brightness-display-apple $(DESTDIR)$(PREFIX)/bin/tam-brightness-display-apple
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-brightness-display-apple/LICENSE
