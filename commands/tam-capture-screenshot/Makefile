PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-screenshot
install:
	install -Dm755 tam-capture-screenshot $(DESTDIR)$(PREFIX)/bin/tam-capture-screenshot
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-screenshot/LICENSE
