PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-audio-source-switch

install:
	install -Dm755 tam-audio-source-switch $(DESTDIR)$(PREFIX)/bin/tam-audio-source-switch
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-source-switch/LICENSE
