.PHONY: clean install

CXX      ?= g++
CXXFLAGS ?= -O2 -Wall -Wextra

asdcontrol: asdcontrol.cpp
	$(CXX) $(CXXFLAGS) asdcontrol.cpp -o asdcontrol

debug: asdcontrol.cpp FORCE
	$(CXX) -Og -g asdcontrol.cpp -o asdcontrol

clean:
	rm -f asdcontrol

install: asdcontrol
	cp asdcontrol /usr/local/bin/asdcontrol

FORCE:
