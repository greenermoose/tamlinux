PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-show-done

install:
	install -Dm755 tam-show-done $(DESTDIR)$(PREFIX)/bin/tam-show-done
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-show-done/LICENSE
