PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-audio-input-set-default
install:
	install -Dm755 tam-audio-input-set-default $(DESTDIR)$(PREFIX)/bin/tam-audio-input-set-default
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-audio-input-set-default/LICENSE
