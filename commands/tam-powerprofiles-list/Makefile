PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-powerprofiles-list
install:
	install -Dm755 tam-powerprofiles-list $(DESTDIR)$(PREFIX)/bin/tam-powerprofiles-list
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-powerprofiles-list/LICENSE
