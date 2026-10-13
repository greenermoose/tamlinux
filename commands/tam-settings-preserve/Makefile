PREFIX ?= /usr/local

.PHONY: check install
check:
	python3 -c "import ast; ast.parse(open('tam-settings-preserve').read())"
install:
	install -Dm755 tam-settings-preserve $(DESTDIR)$(PREFIX)/bin/tam-settings-preserve
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-settings-preserve/LICENSE
