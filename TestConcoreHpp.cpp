/**
 * TestConcoreHpp.cpp
 *
 * Test suite for the Concore class API in concore.hpp.
 * Covers: read_FM/write_FM round-trip, unchanged(), initval(),
 *         mapParser(), default_maxtime(), and tryparam().
 *
 * Addresses Issue #484: adds coverage for the Concore class API.
 *
 * Compile:  g++ -std=c++11 -o TestConcoreHpp TestConcoreHpp.cpp
 * Run:      ./TestConcoreHpp          (Linux/macOS)
 *           TestConcoreHpp.exe        (Windows)
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <cmath>
#include <cstdlib>

#ifdef _WIN32
  #include <direct.h>
  #define MAKE_DIR(p) _mkdir(p)
#else
  #include <sys/stat.h>
  #define MAKE_DIR(p) mkdir(p, 0755)
#endif

#include "concore.hpp"

static int passed = 0;
static int failed = 0;

// ------------- helpers ---------------------------------------------------

static void check(const std::string& testName, bool condition) {
    if (condition) {
        std::cout << "PASS: " << testName << std::endl;
        ++passed;
    } else {
        std::cout << "FAIL: " << testName << std::endl;
        ++failed;
    }
}

static bool approx(double a, double b, double eps = 1e-9) {
    return std::fabs(a - b) < eps;
}

static void write_file(const std::string& path, const std::string& data) {
    std::ofstream f(path);
    f << data;
}

static void rm(const std::string& path) {
    std::remove(path.c_str());
}

static void setup_dirs() {
    MAKE_DIR("in");
    MAKE_DIR("in/1");
    MAKE_DIR("in1");
    MAKE_DIR("out1");
}

// ------------- read_FM ---------------------------------------------------

static void test_read_FM_file() {
    setup_dirs();
    write_file("in1/v", "[3.0,0.5,1.5]");

    Concore c;
    c.delay = 0;
    c.simtime = 0.0;

    std::vector<double> v = c.read_FM(1, "v", "[0.0]");
    check("read_FM size==2",             v.size() == 2);
    check("read_FM[0]==0.5",             approx(v[0], 0.5));
    check("read_FM[1]==1.5",             approx(v[1], 1.5));
    check("read_FM simtime updated",     approx(c.simtime, 3.0));

    rm("in1/v");
}

static void test_read_FM_missing_file_uses_initstr() {
    setup_dirs();
    rm("in1/no_port");

    Concore c;
    c.delay = 0;
    c.simtime = 0.0;

    std::vector<double> v = c.read_FM(1, "no_port", "[9.0,3.0]");
    check("missing_file fallback size==1", v.size() == 1);
    check("missing_file fallback val==3.0", approx(v[0], 3.0));
}

static void test_read_result_missing_file_status() {
    setup_dirs();
    rm("in1/no_port_status");

    Concore c;
    c.delay = 0;
    c.simtime = 0.0;

    Concore::ReadResult r = c.read_result(1, "no_port_status", "[9.0,3.0]");
    check("read_result missing status FILE_NOT_FOUND",
          r.status == Concore::ReadStatus::FILE_NOT_FOUND);
    check("read_result missing uses initstr", r.data.size() == 1 && approx(r.data[0], 3.0));
}

// ------------- write_FM --------------------------------------------------

static void test_write_FM_creates_file() {
    setup_dirs();

    Concore c;
    c.delay = 0;
    c.simtime = 2.0;

    c.write_FM(1, "w_out", {10.0, 20.0});

    std::ifstream f("out1/w_out");
    std::ostringstream ss;
    ss << f.rdbuf();
    std::string content = ss.str();

    check("write_FM file not empty",        !content.empty());
    check("write_FM contains value 10",     content.find("10") != std::string::npos);
    check("write_FM contains simtime 2",    content.find("2")  != std::string::npos);

    rm("out1/w_out");
}

// ------------- unchanged() -----------------------------------------------

static void test_unchanged_after_read_is_false() {
    setup_dirs();
    write_file("in1/uc", "[1.0,0.1]");

    Concore c;
    c.delay = 0;
    c.simtime = 0.0;

    c.read_FM(1, "uc", "[0.0]");
    check("unchanged after read is false", !c.unchanged());

    rm("in1/uc");
}

static void test_unchanged_fresh_object_is_true() {
    Concore c;
    c.delay = 0;
    check("unchanged fresh object is true", c.unchanged());
}

static void test_unchanged_second_call_after_false_is_true() {
    setup_dirs();
    write_file("in1/uc2", "[5.0,7.0]");

    Concore c;
    c.delay = 0;
    c.simtime = 0.0;

    c.read_FM(1, "uc2", "[0.0]");
    c.unchanged();
    bool u = c.unchanged();
    check("unchanged second call is true", u);

    rm("in1/uc2");
}

// ------------- retry exhaustion on empty file ----------------------------

static void test_retry_empty_file_falls_back_to_initstr() {
    setup_dirs();
    write_file("in1/empty_port", "");

    Concore c;
    c.delay = 0;
    c.simtime = 0.0;

    std::vector<double> v = c.read_FM(1, "empty_port", "[7.0,5.0]");
    check("retry exhaustion: initstr used",  v.size() == 1 && approx(v[0], 5.0));
    check("retry exhaustion: retrycount>0",  c.retrycount > 0);

    rm("in1/empty_port");
}

// ------------- initval() -------------------------------------------------

static void test_initval_parses_simtime_and_data() {
    Concore c;
    c.delay = 0;

    std::vector<double> v = c.initval("[4.0,1.0,2.0]");
    check("initval size==2",        v.size() == 2);
    check("initval[0]==1.0",        approx(v[0], 1.0));
    check("initval[1]==2.0",        approx(v[1], 2.0));
    check("initval simtime==4.0",   approx(c.simtime, 4.0));
}

static void test_initval_empty_input_returns_empty() {
    Concore c;
    c.delay = 0;

    std::vector<double> v = c.initval("[]");
    check("initval empty returns empty", v.empty());
}

// ------------- mapParser() -----------------------------------------------

static void test_mapParser_reads_file() {
    setup_dirs();
    write_file("tmp_iport_test.txt", "{'u': 1}");

    Concore c;
    c.delay = 0;

    auto m = c.mapParser("tmp_iport_test.txt");
    check("mapParser has key u",  m.count("u") == 1);
    check("mapParser value==1",   m["u"] == 1);

    rm("tmp_iport_test.txt");
}

static void test_mapParser_missing_file_is_empty() {
    rm("concore_noport_tmp.txt");

    Concore c;
    c.delay = 0;

    auto m = c.mapParser("concore_noport_tmp.txt");
    check("mapParser missing file is empty", m.empty());
}

// ------------- default_maxtime() -----------------------------------------

static void test_default_maxtime_reads_file() {
    setup_dirs();
    write_file("in/1/concore.maxtime", "200");

    Concore c;
    c.delay = 0;
    c.default_maxtime(100);

    check("default_maxtime from file==200", c.maxtime == 200);

    rm("in/1/concore.maxtime");
}

static void test_default_maxtime_fallback() {
    rm("in/1/concore.maxtime");

    Concore c;
    c.delay = 0;
    c.default_maxtime(42);

    check("default_maxtime fallback==42", c.maxtime == 42);
}

// ------------- tryparam() ------------------------------------------------

static void test_tryparam_found() {
    setup_dirs();
    write_file("in/1/concore.params", "{'alpha': '0.5', 'beta': '1.0'}");

    Concore c;
    c.delay = 0;
    c.load_params();

    check("tryparam found alpha",  c.tryparam("alpha", "0.0") == "0.5");
    check("tryparam found beta",   c.tryparam("beta",  "0.0") == "1.0");

    rm("in/1/concore.params");
}

static void test_tryparam_missing_key_uses_default() {
    rm("in/1/concore.params");

    Concore c;
    c.delay = 0;
    c.load_params();

    check("tryparam missing key uses default",
          c.tryparam("no_key", "def_val") == "def_val");
}

static void test_load_params_semicolon_format() {
    setup_dirs();
    write_file("in/1/concore.params", "a=1;b=2");

    Concore c;
    c.delay = 0;
    c.load_params();

    check("load_params semicolon parses a", c.tryparam("a", "") == "1");
    check("load_params semicolon parses b", c.tryparam("b", "") == "2");

    rm("in/1/concore.params");
}

// ------------- main -------------------------------------------------------

int main() {
    std::cout << "===== Concore API Tests (Issue #484) =====\n\n";

    // read_FM / write_FM
    test_read_FM_file();
    test_read_FM_missing_file_uses_initstr();
    test_read_result_missing_file_status();
    test_write_FM_creates_file();

    // unchanged()
    test_unchanged_after_read_is_false();
    test_unchanged_fresh_object_is_true();
    test_unchanged_second_call_after_false_is_true();

    // retry exhaustion on empty file
    test_retry_empty_file_falls_back_to_initstr();

    // initval()
    test_initval_parses_simtime_and_data();
    test_initval_empty_input_returns_empty();

    // mapParser()
    test_mapParser_reads_file();
    test_mapParser_missing_file_is_empty();

    // default_maxtime()
    test_default_maxtime_reads_file();
    test_default_maxtime_fallback();

    // tryparam()
    test_tryparam_found();
    test_tryparam_missing_key_uses_default();
    test_load_params_semicolon_format();

    std::cout << "\n=== Results: " << passed << " passed, " << failed
              << " failed out of " << (passed + failed) << " tests ===\n";

    return (failed > 0) ? 1 : 0;
}
