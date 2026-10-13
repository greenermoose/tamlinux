PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-obsidian
install:
	install -Dm755 tam-theme-set-obsidian $(DESTDIR)$(PREFIX)/bin/tam-theme-set-obsidian
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-obsidian/LICENSE
