PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set-tmux
install:
	install -Dm755 tam-theme-set-tmux $(DESTDIR)$(PREFIX)/bin/tam-theme-set-tmux
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set-tmux/LICENSE
