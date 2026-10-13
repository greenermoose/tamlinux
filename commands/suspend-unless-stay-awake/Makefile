PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n suspend-unless-stay-awake
install:
	install -Dm755 suspend-unless-stay-awake $(DESTDIR)$(PREFIX)/bin/suspend-unless-stay-awake
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/suspend-unless-stay-awake/LICENSE
