PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-webcam-resize
install:
	install -Dm755 tam-capture-webcam-resize $(DESTDIR)$(PREFIX)/bin/tam-capture-webcam-resize
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-webcam-resize/LICENSE
