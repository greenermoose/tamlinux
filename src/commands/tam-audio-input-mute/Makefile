PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-audio-input-mute

install:
	install -Dm755 tam-audio-input-mute $(DESTDIR)$(PREFIX)/bin/tam-audio-input-mute
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-input-mute/LICENSE
