PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-suspend-unless-stay-awake
	bash tests/test-sleep-choice.sh
install:
	install -Dm755 tam-suspend-unless-stay-awake $(DESTDIR)$(PREFIX)/bin/tam-suspend-unless-stay-awake
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-suspend-unless-stay-awake/LICENSE
