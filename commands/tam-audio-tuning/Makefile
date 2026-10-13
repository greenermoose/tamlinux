PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-tuning
install:
	install -Dm755 tam-audio-tuning $(DESTDIR)$(PREFIX)/bin/tam-audio-tuning
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-tuning/LICENSE
	install -d $(DESTDIR)$(PREFIX)/share/tamlinux/audio
	cp -R ../../desktop/audio/. $(DESTDIR)$(PREFIX)/share/tamlinux/audio/
