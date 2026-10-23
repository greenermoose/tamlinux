PREFIX ?= /usr/local
.PHONY: check install
check:
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
install:
	install -Dm755 tam-monitor $(DESTDIR)$(PREFIX)/bin/tam-monitor
	install -Dm644 README.md $(DESTDIR)$(PREFIX)/share/doc/tam-monitor/README.md
	install -Dm644 ../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-monitor/LICENSE
