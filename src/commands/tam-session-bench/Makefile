PREFIX ?= /usr/local

.PHONY: check install

check:
	PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -v

install:
	install -Dm755 tam-session-bench $(DESTDIR)$(PREFIX)/bin/tam-session-bench
	install -Dm644 README $(DESTDIR)$(PREFIX)/share/doc/tam-session-bench/README
