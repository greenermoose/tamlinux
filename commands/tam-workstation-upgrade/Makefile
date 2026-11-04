PREFIX ?= /usr/local
LIBEXEC ?= $(PREFIX)/libexec/tam-workstation-upgrade

.PHONY: check install
check:
	python3 -B -m unittest discover -s tests -v

install:
	install -d $(DESTDIR)$(LIBEXEC)
	install -Dm644 cli.py $(DESTDIR)$(LIBEXEC)/cli.py
	install -Dm644 release.py $(DESTDIR)$(LIBEXEC)/release.py
	install -Dm644 host.py $(DESTDIR)$(LIBEXEC)/host.py
	install -Dm644 compat.py $(DESTDIR)$(LIBEXEC)/compat.py
	install -Dm644 receipt.py $(DESTDIR)$(LIBEXEC)/receipt.py
	install -Dm755 tam-workstation-upgrade $(DESTDIR)$(PREFIX)/bin/tam-workstation-upgrade
