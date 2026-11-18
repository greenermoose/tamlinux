# The workstation build uses local Git objects. Distribution adapters can
# still build and stage the product independently with an explicit prefix.
.DEFAULT_GOAL := source
REPOS ?= ..
SOURCE_BUILD ?= scratch/source-install
SOURCE_INSTALL := desktop/source-install/main.py
ifeq ($(origin PREFIX)$(origin DESTDIR),undefinedundefined)
.PHONY: source preflight source-delivery install
source:
	/usr/bin/python3 -I $(SOURCE_INSTALL) build --repos "$(REPOS)" --work "$(SOURCE_BUILD)"

preflight:
	/usr/bin/python3 -I -B $(SOURCE_INSTALL) preflight --repos "$(REPOS)" --work "$(SOURCE_BUILD)" $(if $(SOURCE_ROOT),--root "$(SOURCE_ROOT)")

source-delivery:
	@/usr/bin/python3 -I -B $(SOURCE_INSTALL) delivery --repos "$(REPOS)" --work "$(SOURCE_BUILD)"

install:
ifneq ($(strip $(SOURCE_PLAN)),)
	/usr/bin/python3 -I -B desktop/source-install/transaction.py install --plan "$(SOURCE_PLAN)"
else
	/usr/bin/python3 -I $(SOURCE_INSTALL) install --repos "$(REPOS)" --work "$(SOURCE_BUILD)" $(if $(SOURCE_ROOT),--root "$(SOURCE_ROOT)")
endif
else
.DEFAULT_GOAL := all
.PHONY: install
install: install-product
endif

PREFIX ?= /usr/local
PYTHON ?= python3
NATIVE_COMMANDS := start tam-boot tam-hardware tam-launch-journal tam-meter tam-monitor tam-open

.PHONY: all install-product install-commands install-data install-bundle check-install $(NATIVE_COMMANDS)
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

install-product: install-commands install-data

install-bundle:
	$(PYTHON) -I desktop/install-bundle-layout.py --check --prefix "$(PREFIX)" --destdir "$(DESTDIR)"
	$(MAKE) install-product PREFIX="$(PREFIX)" DESTDIR="$(DESTDIR)"
	$(PYTHON) -I desktop/install-bundle-layout.py --prefix "$(PREFIX)" --destdir "$(DESTDIR)"

check-install:
	$(PYTHON) -B -m unittest discover -s desktop/tests -p test_product_install.py -v
