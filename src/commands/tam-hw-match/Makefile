PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-hw-match
install:
	install -Dm755 tam-hw-match $(DESTDIR)$(PREFIX)/bin/tam-hw-match
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-hw-match/LICENSE
