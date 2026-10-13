PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-webcam-list
install:
	install -Dm755 tam-capture-webcam-list $(DESTDIR)$(PREFIX)/bin/tam-capture-webcam-list
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-webcam-list/LICENSE
