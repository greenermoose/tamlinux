PREFIX ?= /usr/local
.PHONY: check install
check:
	bash -n tam-theme-set
	@if [ -z "$(TAM_CHECK_ALL)" ]; then \
		python3 -B -m unittest discover -s ../../../tests -p test_theme_ownership.py -q; \
	fi
	python3 -B -m unittest discover -s tests -p test_gtk4_adapter.py -q
install:
	install -Dm755 tam-theme-set $(DESTDIR)$(PREFIX)/bin/tam-theme-set
	install -Dm644 ../../../LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-theme-set/LICENSE
	install -Dm644 ../../desktop/theme/engine.py $(DESTDIR)$(PREFIX)/share/tamlinux/theme/engine.py
