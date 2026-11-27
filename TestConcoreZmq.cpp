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

// Plain REP socket on the other end, so tests can see the exact bytes sent.
struct RepPeer {
    zmq::context_t ctx{1};
    zmq::socket_t sock{ctx, ZMQ_REP};

    explicit RepPeer(const std::string& address) {
        sock.set(zmq::sockopt::linger, 0);
        sock.set(zmq::sockopt::rcvtimeo, 2000);
        sock.bind(address);
    }
    std::string recv() {
        zmq::message_t m;
        auto res = sock.recv(m, zmq::recv_flags::none);
        return res ? m.to_string() : std::string("<timeout>");
    }
    void send(const std::string& s) {
        try {
            sock.send(zmq::buffer(s), zmq::send_flags::none);
        } catch (const zmq::error_t&) {}  // out of step when the REQ side is stuck
    }
};

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

// The two write_zmq cases from tests/protocol_fixtures/python_phase1_cases.json
static void test_write_zmq_fixture_cases() {
    RepPeer peer("tcp://127.0.0.1:5593");
    Concore c;
    c.init_zmq_port("p", "connect", "tcp://127.0.0.1:5593", "REQ");
    c.simtime = 10;
    c.write("p", "data", std::vector<double>{1.5, 2.5}, 2);
    check("list payload gets simtime+delta in front", peer.recv() == "[12, 1.5, 2.5]");
    check("list write leaves simtime alone", approx(c.simtime, 10));

#ifndef TEST_DOCKER_HEADER  // concoredocker.hpp has no string write
    peer.send("[0]");
    c.read("p", "ack", "[0]");
    c.simtime = 10;
    c.delay = 0;
    c.write("p", "status", std::string("ok"), 3);
    check("string payload is sent as is", peer.recv() == "ok");
    check("string write leaves simtime alone", approx(c.simtime, 10));
#endif
}

// Same scenario as the Python test for issue #598: the reply to the first
// request never comes, the REQ port must still be able to send again.
static void test_req_recovers_after_missing_reply() {
    RepPeer peer("tcp://127.0.0.1:5592");
    concore_base::ZeroMQPort req("connect", "tcp://127.0.0.1:5592", ZMQ_REQ);
    req.socket.set(zmq::sockopt::rcvtimeo, 50);

    req.send_with_retry({0, 1});
    check("first request arrives", peer.recv() == "[0, 1]");
    check("missing reply times out", req.recv_with_retry().empty());

    req.send_with_retry({0, 2});
    peer.send("[0, 99]");  // late reply to the first request
    check("second request arrives", peer.recv() == "[0, 2]");
    peer.send("[0, 7]");

    req.socket.set(zmq::sockopt::rcvtimeo, 2000);
    std::vector<double> reply = req.recv_with_retry();
    check("late reply is dropped", reply.size() == 2 && approx(reply[1], 7));
}

int main() {
    test_round_trip();
    test_write_zmq_fixture_cases();
    test_req_recovers_after_missing_reply();
    std::cout << "\n" << passed << " passed, " << failed << " failed" << std::endl;
    return failed ? 1 : 0;
}
