PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-capture-screenrecording-with-webcam
install:
	install -Dm755 tam-capture-screenrecording-with-webcam $(DESTDIR)$(PREFIX)/bin/tam-capture-screenrecording-with-webcam
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-capture-screenrecording-with-webcam/LICENSE
