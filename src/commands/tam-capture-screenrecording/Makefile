PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-screenrecording
install:
	install -Dm755 tam-capture-screenrecording $(DESTDIR)$(PREFIX)/bin/tam-capture-screenrecording
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-screenrecording/LICENSE
