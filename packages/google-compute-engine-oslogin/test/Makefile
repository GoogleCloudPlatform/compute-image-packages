TOPDIR = $(realpath ..)

CPPFLAGS += -I$(TOPDIR)/src/include -I/usr/include/json-c
CXXFLAGS += -g -Wall -Wextra -std=c++11
LDLIBS = -lcurl -ljson-c -lpthread

all : test_runner non_network_tests

clean :
	rm -f test_runner *.o

gtest-all.o : $(GTEST_DIR)/src/gtest-all.cc
	$(CXX) $(CXXFLAGS) -isystem $(GTEST)/include -I$(GTEST) $(CPPFLAGS) -c $^

test_runner : oslogin_utils_test.o $(TOPDIR)/src/utils.o gtest-all.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $^ -o $@ $(LDLIBS)

non_network_tests : test_runner
	./test_runner --gtest_filter=*-FindGroupTest.*:GetUsersForGroupTest.*

network_tests : test_runner ping reset
	./test_runner --gtest_filter=FindGroupTest.*:GetUsersForGroupTest.*

# run as $ make tests GTESTARGS="--gtest_filter=FindGroupTest.*"
tests : test_runner
	./test_runner ${GTESTARGS}

ping :
	nc -vzw2 metadata.google.internal 80 >/dev/null 2>&1

reset :
	curl -Ss http://metadata.google.internal/reset >/dev/null 2>&1

.PHONY : all clean tests ping reset gtest prowtest
