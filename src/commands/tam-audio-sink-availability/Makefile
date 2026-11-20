PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-sink-availability
install:
	install -Dm755 tam-audio-sink-availability $(DESTDIR)$(PREFIX)/bin/tam-audio-sink-availability
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-sink-availability/LICENSE
