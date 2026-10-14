PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-toggle-hybrid-gpu

install:
	install -Dm755 tam-toggle-hybrid-gpu $(DESTDIR)$(PREFIX)/bin/tam-toggle-hybrid-gpu
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-toggle-hybrid-gpu/LICENSE
