PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-output-volume
install:
	install -Dm755 tam-audio-output-volume $(DESTDIR)$(PREFIX)/bin/tam-audio-output-volume
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-output-volume/LICENSE
