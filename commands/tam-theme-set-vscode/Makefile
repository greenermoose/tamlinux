PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-vscode
install:
	install -Dm755 tam-theme-set-vscode $(DESTDIR)$(PREFIX)/bin/tam-theme-set-vscode
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-vscode/LICENSE
