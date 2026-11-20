PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-chromium-ytdlp-host
install:
	install -Dm755 tam-chromium-ytdlp-host $(DESTDIR)$(PREFIX)/bin/tam-chromium-ytdlp-host
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-chromium-ytdlp-host/LICENSE
