PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-output-set-default
install:
	install -Dm755 tam-audio-output-set-default $(DESTDIR)$(PREFIX)/bin/tam-audio-output-set-default
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-output-set-default/LICENSE
