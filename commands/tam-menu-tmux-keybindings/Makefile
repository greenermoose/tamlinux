PREFIX ?= /usr/local

.PHONY: check install

check:
	bash -n tam-menu-tmux-keybindings

install:
	install -Dm755 tam-menu-tmux-keybindings $(DESTDIR)$(PREFIX)/bin/tam-menu-tmux-keybindings
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-menu-tmux-keybindings/LICENSE
