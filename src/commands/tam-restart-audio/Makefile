PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-restart-audio
install:
	install -Dm755 tam-restart-audio $(DESTDIR)$(PREFIX)/bin/tam-restart-audio
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-audio/LICENSE
