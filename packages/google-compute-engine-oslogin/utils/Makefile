CPPFLAGS += -I/usr/include/json-c
CXXFLAGS += -g -Wall -Wextra -std=c++11
LDLIBS = -lcurl -ljson-c -lgtest -lpthread

all : test_runner non_network_tests

clean :
	rm -f test_runner *.o

test_runner : oslogin_utils_test.o oslogin_utils.o
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $^ -o $@ $(LDLIBS)

oslogin_utils_test.o oslogin_utils.o : oslogin_utils_test.cc oslogin_utils.cc oslogin_utils.h
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c oslogin_utils_test.cc oslogin_utils.cc

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
