/**
 * TestLiteralEvalCpp.cpp
 *
 * Test suite for the C++ Python-literal-compatible parser in concore_base.hpp.
 * Validates Issue #389 fix: C++ parser must accept all valid concore payloads
 * that Python's ast.literal_eval() accepts.
 *
 * Compile:  g++ -std=c++11 -o TestLiteralEvalCpp TestLiteralEvalCpp.cpp
 * Run:      ./TestLiteralEvalCpp          (Linux/macOS)
 *           TestLiteralEvalCpp.exe        (Windows)
 */

#include <iostream>
#include <string>
#include <vector>
#include <cmath>
#include <cstdlib>
#include <stdexcept>

#include "concore_base.hpp"

using namespace concore_base;

static int passed = 0;
static int failed = 0;

// ------------- helpers -------------------------------------------------

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

// ------------- backward-compatibility tests ----------------------------

static void test_flat_numeric_list() {
    std::vector<double> v = parselist_double("[10.0, 0.5, 2.3]");
    check("flat_numeric size==3", v.size() == 3);
    check("flat_numeric[0]==10.0", approx(v[0], 10.0));
    check("flat_numeric[1]==0.5",  approx(v[1], 0.5));
    check("flat_numeric[2]==2.3",  approx(v[2], 2.3));
}

static void test_empty_list() {
    std::vector<double> v = parselist_double("[]");
    check("empty_list size==0", v.size() == 0);
}

static void test_single_element() {
    std::vector<double> v = parselist_double("[42.0]");
    check("single_element size==1", v.size() == 1);
    check("single_element[0]==42", approx(v[0], 42.0));
}

static void test_negative_numbers() {
    std::vector<double> v = parselist_double("[-1.5, -3.0, 2.0]");
    check("negative size==3", v.size() == 3);
    check("negative[0]==-1.5", approx(v[0], -1.5));
    check("negative[1]==-3.0", approx(v[1], -3.0));
}

static void test_scientific_notation() {
    std::vector<double> v = parselist_double("[1e3, 2.5E-2, -1.0e+1]");
    check("sci size==3", v.size() == 3);
    check("sci[0]==1000", approx(v[0], 1000.0));
    check("sci[1]==0.025", approx(v[1], 0.025));
    check("sci[2]==-10",  approx(v[2], -10.0));
}

static void test_integer_values() {
    std::vector<double> v = parselist_double("[1, 2, 3]");
    check("int size==3", v.size() == 3);
    check("int[0]==1", approx(v[0], 1.0));
    check("int[2]==3", approx(v[2], 3.0));
}

// ------------- mixed-type payload tests (Issue #389 core) --------------

static void test_string_element() {
    // [10.0, "start", 0.5]  –  string should be skipped in numeric flatten
    std::vector<double> v = parselist_double("[10.0, \"start\", 0.5]");
    check("string_elem size==2", v.size() == 2);
    check("string_elem[0]==10.0", approx(v[0], 10.0));
    check("string_elem[1]==0.5",  approx(v[1], 0.5));
}

static void test_boolean_element() {
    // [10.0, True, 0.5]
    std::vector<double> v = parselist_double("[10.0, True, 0.5]");
    check("bool_elem size==3", v.size() == 3);
    check("bool_elem[0]==10.0", approx(v[0], 10.0));
    check("bool_elem[1]==1.0 (True)", approx(v[1], 1.0));
    check("bool_elem[2]==0.5", approx(v[2], 0.5));
}

static void test_bool_false() {
    std::vector<double> v = parselist_double("[False, 5.0]");
    check("bool_false size==2", v.size() == 2);
    check("bool_false[0]==0.0", approx(v[0], 0.0));
}

static void test_nested_list() {
    // [10.0, [0.5, 0.3], 0.1]  –  nested list flattened to [10.0, 0.5, 0.3, 0.1]
    std::vector<double> v = parselist_double("[10.0, [0.5, 0.3], 0.1]");
    check("nested size==4", v.size() == 4);
    check("nested[0]==10.0", approx(v[0], 10.0));
    check("nested[1]==0.5",  approx(v[1], 0.5));
    check("nested[2]==0.3",  approx(v[2], 0.3));
    check("nested[3]==0.1",  approx(v[3], 0.1));
}

static void test_tuple_payload() {
    // (10.0, 0.3)  –  tuple treated as array
    std::vector<double> v = parselist_double("(10.0, 0.3)");
    check("tuple size==2", v.size() == 2);
    check("tuple[0]==10.0", approx(v[0], 10.0));
    check("tuple[1]==0.3",  approx(v[1], 0.3));
}

static void test_nested_tuple() {
    // [10.0, (0.5, 0.3)]
    std::vector<double> v = parselist_double("[10.0, (0.5, 0.3)]");
    check("nested_tuple size==3", v.size() == 3);
    check("nested_tuple[0]==10.0", approx(v[0], 10.0));
    check("nested_tuple[1]==0.5",  approx(v[1], 0.5));
    check("nested_tuple[2]==0.3",  approx(v[2], 0.3));
}

static void test_mixed_types() {
    // [10.0, "label", True, [1, 2], (3,), False, "end"]
    std::vector<double> v = parselist_double("[10.0, \"label\", True, [1, 2], (3,), False, \"end\"]");
    // numeric values: 10.0, 1.0(True), 1, 2, 3, 0.0(False) = 6 values
    check("mixed size==6", v.size() == 6);
    check("mixed[0]==10.0",   approx(v[0], 10.0));
    check("mixed[1]==1.0",    approx(v[1], 1.0));   // True
    check("mixed[2]==1.0",    approx(v[2], 1.0));   // nested [1,...]
    check("mixed[3]==2.0",    approx(v[3], 2.0));   // nested [...,2]
    check("mixed[4]==3.0",    approx(v[4], 3.0));   // tuple (3,)
    check("mixed[5]==0.0",    approx(v[5], 0.0));   // False
}

// ------------- full ConcoreValue parse tests ---------------------------

static void test_parse_literal_string() {
    ConcoreValue v = parse_literal("[10.0, \"start\", 0.5]");
    check("literal_string is ARRAY", v.type == ConcoreValueType::ARRAY);
    check("literal_string len==3", v.array.size() == 3);
    check("literal_string[0] NUMBER", v.array[0].type == ConcoreValueType::NUMBER);
    check("literal_string[1] STRING", v.array[1].type == ConcoreValueType::STRING);
    check("literal_string[1]==\"start\"", v.array[1].str == "start");
    check("literal_string[2] NUMBER", v.array[2].type == ConcoreValueType::NUMBER);
}

static void test_parse_literal_bool() {
    ConcoreValue v = parse_literal("[True, False]");
    check("literal_bool is ARRAY", v.type == ConcoreValueType::ARRAY);
    check("literal_bool[0] BOOL", v.array[0].type == ConcoreValueType::BOOL);
    check("literal_bool[0]==true", v.array[0].boolean == true);
    check("literal_bool[1]==false", v.array[1].boolean == false);
}

static void test_parse_literal_nested() {
    ConcoreValue v = parse_literal("[1, [2, [3]]]");
    check("literal_nested outer ARRAY", v.type == ConcoreValueType::ARRAY);
    check("literal_nested[1] ARRAY", v.array[1].type == ConcoreValueType::ARRAY);
    check("literal_nested[1][1] ARRAY", v.array[1].array[1].type == ConcoreValueType::ARRAY);
    check("literal_nested[1][1][0]==3", approx(v.array[1].array[1].array[0].number, 3.0));
}

static void test_parse_single_quoted_string() {
    ConcoreValue v = parse_literal("['hello']");
    check("single_quote ARRAY", v.type == ConcoreValueType::ARRAY);
    check("single_quote[0] STRING", v.array[0].type == ConcoreValueType::STRING);
    check("single_quote[0]=='hello'", v.array[0].str == "hello");
}

static void test_parse_escape_sequences() {
    ConcoreValue v = parse_literal("[\"line\\none\"]");
    check("escape STRING", v.array[0].type == ConcoreValueType::STRING);
    check("escape has newline", v.array[0].str == "line\none");
}

static void test_parse_none() {
    ConcoreValue v = parse_literal("[None, 1]");
    check("none[0] STRING", v.array[0].type == ConcoreValueType::STRING);
    check("none[0]==\"None\"", v.array[0].str == "None");
}

static void test_trailing_comma() {
    // Python allows trailing comma: [1, 2,]
    std::vector<double> v = parselist_double("[1, 2,]");
    check("trailing_comma size==2", v.size() == 2);
    check("trailing_comma[1]==2", approx(v[1], 2.0));
}

// ------------- error / failure case tests ------------------------------

static void test_malformed_bracket() {
    bool caught = false;
    try {
        parse_literal("[1, 2");
    } catch (const std::runtime_error&) {
        caught = true;
    }
    check("malformed_bracket throws", caught);
}

static void test_malformed_string() {
    bool caught = false;
    try {
        parse_literal("[\"unterminated]");
    } catch (const std::runtime_error&) {
        caught = true;
    }
    check("malformed_string throws", caught);
}

static void test_unsupported_object() {
    bool caught = false;
    try {
        parse_literal("{1: 2}");
    } catch (const std::runtime_error&) {
        caught = true;
    }
    check("unsupported_object throws", caught);
}

static void test_empty_string_input() {
    std::vector<double> v = parselist_double("");
    check("empty_input size==0", v.size() == 0);
}

// ------------- cross-language round-trip tests -------------------------

static void test_python_write_cpp_read_flat() {
    // Simulate Python write: "[5.0, 1.0, 2.0]"
    std::vector<double> v = parselist_double("[5.0, 1.0, 2.0]");
    check("py2cpp_flat size==3", v.size() == 3);
    check("py2cpp_flat[0]==5.0", approx(v[0], 5.0));
}

static void test_python_write_cpp_read_mixed() {
    // Simulate Python write: "[5.0, 'sensor_a', True, [0.1, 0.2]]"
    std::vector<double> v = parselist_double("[5.0, 'sensor_a', True, [0.1, 0.2]]");
    // numeric: 5.0, 1.0(True), 0.1, 0.2 = 4
    check("py2cpp_mixed size==4", v.size() == 4);
    check("py2cpp_mixed[0]==5.0", approx(v[0], 5.0));
    check("py2cpp_mixed[1]==1.0", approx(v[1], 1.0));
    check("py2cpp_mixed[2]==0.1", approx(v[2], 0.1));
    check("py2cpp_mixed[3]==0.2", approx(v[3], 0.2));
}

// ------------- main ----------------------------------------------------

int main() {
    std::cout << "===== C++ Literal Parser Tests (Issue #389) =====\n\n";

    // Backward compatibility
    test_flat_numeric_list();
    test_empty_list();
    test_single_element();
    test_negative_numbers();
    test_scientific_notation();
    test_integer_values();

    // Mixed-type payloads (core of Issue #389)
    test_string_element();
    test_boolean_element();
    test_bool_false();
    test_nested_list();
    test_tuple_payload();
    test_nested_tuple();
    test_mixed_types();

    // Full ConcoreValue structure tests
    test_parse_literal_string();
    test_parse_literal_bool();
    test_parse_literal_nested();
    test_parse_single_quoted_string();
    test_parse_escape_sequences();
    test_parse_none();
    test_trailing_comma();

    // Error / failure cases
    test_malformed_bracket();
    test_malformed_string();
    test_unsupported_object();
    test_empty_string_input();

    // Cross-language round-trip
    test_python_write_cpp_read_flat();
    test_python_write_cpp_read_mixed();

    std::cout << "\n=== Results: " << passed << " passed, " << failed
              << " failed out of " << (passed + failed) << " tests ===\n";

    return (failed > 0) ? 1 : 0;
}
