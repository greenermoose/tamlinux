PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-webapp-handler-hey
	python3 -B -m unittest discover -s tests -v

install:
	install -Dm755 tam-webapp-handler-hey $(DESTDIR)$(PREFIX)/bin/tam-webapp-handler-hey
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-webapp-handler-hey/LICENSE
