PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-webapp-handler-zoom
	python3 -B -m unittest discover -s tests -q

install:
	install -Dm755 tam-webapp-handler-zoom $(DESTDIR)$(PREFIX)/bin/tam-webapp-handler-zoom
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-webapp-handler-zoom/LICENSE
