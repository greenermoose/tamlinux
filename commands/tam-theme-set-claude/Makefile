PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-claude
install:
	install -Dm755 tam-theme-set-claude $(DESTDIR)$(PREFIX)/bin/tam-theme-set-claude
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-claude/LICENSE
