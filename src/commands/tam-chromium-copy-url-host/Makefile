PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-chromium-copy-url-host
install:
	install -Dm755 tam-chromium-copy-url-host $(DESTDIR)$(PREFIX)/bin/tam-chromium-copy-url-host
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-chromium-copy-url-host/LICENSE
