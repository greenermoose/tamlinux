PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-output-sink
install:
	install -Dm755 tam-audio-output-sink $(DESTDIR)$(PREFIX)/bin/tam-audio-output-sink
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-output-sink/LICENSE
