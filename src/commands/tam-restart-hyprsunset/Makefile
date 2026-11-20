PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-restart-hyprsunset
install:
	install -Dm755 tam-restart-hyprsunset $(DESTDIR)$(PREFIX)/bin/tam-restart-hyprsunset
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-hyprsunset/LICENSE
