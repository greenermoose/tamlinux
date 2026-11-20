PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-transcode-ascii
install:
	install -Dm755 tam-transcode-ascii $(DESTDIR)$(PREFIX)/bin/tam-transcode-ascii
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-transcode-ascii/LICENSE
