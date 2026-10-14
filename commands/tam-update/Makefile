PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-update
	python3 -B -m unittest discover -s tests -q
install:
	install -Dm755 tam-update $(DESTDIR)$(PREFIX)/bin/tam-update
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-update/LICENSE
