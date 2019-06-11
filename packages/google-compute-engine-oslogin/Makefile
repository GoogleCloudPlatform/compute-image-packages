all install :
	$(MAKE) -C src $@

tests :
	$(MAKE) -C test $@

clean :
	$(MAKE) -C src clean
	$(MAKE) -C test clean

prowbuild : debian_deps all

prowtest : debian_deps tests

debian_deps :
	sudo apt-get -y install g++ libcurl4-openssl-dev libjson-c-dev libpam-dev \
		googletest && touch $@

.PHONY : all clean install prowbuild prowtest
