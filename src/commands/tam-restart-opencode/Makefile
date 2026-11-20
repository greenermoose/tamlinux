PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-restart-opencode
install:
	install -Dm755 tam-restart-opencode $(DESTDIR)$(PREFIX)/bin/tam-restart-opencode
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-restart-opencode/LICENSE
