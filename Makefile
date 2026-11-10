# Native product build, shared by tam-bundle recipes and distribution builds.
# Third-party software, fonts and system integration belong to the adapter.
PREFIX ?= /usr/local
PYTHON ?= python3
NATIVE_COMMANDS := start tam-boot tam-hardware tam-meter tam-monitor tam-open

.PHONY: all install install-commands install-data install-bundle check-install $(NATIVE_COMMANDS)
all: $(NATIVE_COMMANDS)

$(NATIVE_COMMANDS):
	$(MAKE) -C commands/$@ all PREFIX=$(PREFIX)

install-commands: all
	@set -e; for dir in commands/*; do \
		test -f "$$dir/Makefile" || continue; \
		$(MAKE) -C "$$dir" install PREFIX="$(PREFIX)" DESTDIR="$(DESTDIR)"; \
	done

install-data:
	$(PYTHON) -I desktop/install-product.py --prefix "$(PREFIX)" --destdir "$(DESTDIR)"

install: install-commands install-data

install-bundle:
	$(PYTHON) -I desktop/install-bundle-layout.py --check --prefix "$(PREFIX)" --destdir "$(DESTDIR)"
	$(MAKE) install PREFIX="$(PREFIX)" DESTDIR="$(DESTDIR)"
	$(PYTHON) -I desktop/install-bundle-layout.py --prefix "$(PREFIX)" --destdir "$(DESTDIR)"

check-install:
	$(PYTHON) -B -m unittest discover -s desktop/tests -p test_product_install.py -v
