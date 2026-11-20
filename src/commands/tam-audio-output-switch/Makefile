PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-output-switch
install:
	install -Dm755 tam-audio-output-switch $(DESTDIR)$(PREFIX)/bin/tam-audio-output-switch
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-output-switch/LICENSE
