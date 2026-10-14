PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-transcode

install:
	install -Dm755 tam-transcode $(DESTDIR)$(PREFIX)/bin/tam-transcode
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-transcode/LICENSE
