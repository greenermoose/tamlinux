PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-webapp-handler-zoom

install:
	install -Dm755 tam-webapp-handler-zoom $(DESTDIR)$(PREFIX)/bin/tam-webapp-handler-zoom
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-webapp-handler-zoom/LICENSE
