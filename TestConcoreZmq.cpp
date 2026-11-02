/**
 * TestConcoreZmq.cpp
 *
 * Tests for the C++ ZMQ transport (CONCORE_USE_ZMQ).
 *
 * Compile:  g++ -std=c++11 -DCONCORE_USE_ZMQ -I. -o TestConcoreZmq TestConcoreZmq.cpp -lzmq
 * Add -DTEST_DOCKER_HEADER to run the same tests against concoredocker.hpp.
 */

#include <iostream>
#include <string>
#include <vector>
#include <cmath>

#ifdef TEST_DOCKER_HEADER
#include "concoredocker.hpp"
#else
#include "concore.hpp"
#endif

static int passed = 0;
static int failed = 0;

static void check(const std::string& testName, bool condition) {
    if (condition) {
        std::cout << "PASS: " << testName << std::endl;
        ++passed;
    } else {
        std::cout << "FAIL: " << testName << std::endl;
        ++failed;
    }
}

static bool approx(double a, double b) { return std::fabs(a - b) < 1e-9; }

static void test_round_trip() {
    Concore server, client;
    server.init_zmq_port("p", "bind", "tcp://127.0.0.1:5591", "REP");
    client.init_zmq_port("p", "connect", "tcp://127.0.0.1:5591", "REQ");

    client.simtime = 3;
    client.write("p", "u", std::vector<double>{1.5, 2.5}, 1);
    std::vector<double> u = server.read("p", "u", "[0.0]");
    check("request values arrive", u.size() == 2 && approx(u[0], 1.5) && approx(u[1], 2.5));
    check("request timestamp moves server simtime", approx(server.simtime, 4));

    server.write("p", "ym", std::vector<double>{9}, 0);
    std::vector<double> ym = client.read("p", "ym", "[0.0]");
    check("reply values arrive", ym.size() == 1 && approx(ym[0], 9));
    check("client simtime after reply", approx(client.simtime, 4));
}

int main() {
    test_round_trip();
    std::cout << "\n" << passed << " passed, " << failed << " failed" << std::endl;
    return failed ? 1 : 0;
}
