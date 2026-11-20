PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-powerprofiles-set
install:
	install -Dm755 tam-powerprofiles-set $(DESTDIR)$(PREFIX)/bin/tam-powerprofiles-set
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-powerprofiles-set/LICENSE
