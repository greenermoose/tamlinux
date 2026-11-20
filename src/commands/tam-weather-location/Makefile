PREFIX ?= /usr/local

.PHONY: check install
check:
	bash -n tam-weather-location
install:
	install -Dm755 tam-weather-location $(DESTDIR)$(PREFIX)/bin/tam-weather-location
	install -Dm644 LICENSE $(DESTDIR)$(PREFIX)/share/licenses/tam-weather-location/LICENSE
