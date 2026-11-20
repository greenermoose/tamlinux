PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-hw-hybrid-gpu

install:
	install -Dm755 tam-hw-hybrid-gpu $(DESTDIR)$(PREFIX)/bin/tam-hw-hybrid-gpu
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-hybrid-gpu/LICENSE
