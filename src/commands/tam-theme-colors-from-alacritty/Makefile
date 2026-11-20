PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-colors-from-alacritty
install:
	install -Dm755 tam-theme-colors-from-alacritty $(DESTDIR)$(PREFIX)/bin/tam-theme-colors-from-alacritty
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-colors-from-alacritty/LICENSE
