PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-dns
	python3 -c 'import ast; ast.parse(open("dns_recovery.py").read())'
install:
	install -Dm755 tam-dns $(DESTDIR)$(PREFIX)/bin/tam-dns
	install -Dm644 dns_recovery.py $(DESTDIR)$(PREFIX)/share/tamlinux/native/dns_recovery.py
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-dns/LICENSE
