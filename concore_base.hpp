// concore_base.hpp -- shared utilities for concore.hpp and concoredocker.hpp
// Extracted to eliminate drift between local and Docker C++ implementations.
#ifndef CONCORE_BASE_HPP
#define CONCORE_BASE_HPP

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <vector>
#include <chrono>
#include <thread>
#include <regex>
#include <algorithm>
#include <cstring>
#include <stdexcept>
#include <cctype>

namespace concore_base {

// ===================================================================
// String Helpers
// ===================================================================
inline std::string stripstr(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

inline std::string stripquotes(const std::string& str) {
    if (str.size() >= 2 &&
        ((str.front() == '\'' && str.back() == '\'') ||
         (str.front() == '"'  && str.back() == '"')))
        return str.substr(1, str.size() - 2);
    return str;
}

// ===================================================================
// Parsing Utilities
// ===================================================================

/**
 * Parses a Python-style dict string into a string→string map.
 * Format: {'key1': val1, 'key2': val2}
 * Handles both quoted and unquoted keys/values.
 */
inline std::map<std::string, std::string> parsedict(const std::string& str) {
    std::map<std::string, std::string> result;
    std::string trimmed = stripstr(str);
    if (trimmed.size() < 2 || trimmed.front() != '{' || trimmed.back() != '}')
        return result;
    std::string inner = trimmed.substr(1, trimmed.size() - 2);
    std::stringstream ss(inner);
    std::string token;
    while (std::getline(ss, token, ',')) {
        size_t colon = token.find(':');
        if (colon == std::string::npos) continue;
        std::string key = stripquotes(stripstr(token.substr(0, colon)));
        std::string val = stripquotes(stripstr(token.substr(colon + 1)));
        if (!key.empty()) result[key] = val;
    }
    return result;
}

/**
 * Parses a Python-style list string into a vector of strings.
 * Format: [val1, val2, val3]
 */
inline std::vector<std::string> parselist(const std::string& str) {
    std::vector<std::string> result;
    std::string trimmed = stripstr(str);
    if (trimmed.size() < 2 || trimmed.front() != '[' || trimmed.back() != ']')
        return result;
    std::string inner = trimmed.substr(1, trimmed.size() - 2);
    std::stringstream ss(inner);
    std::string token;
    while (std::getline(ss, token, ',')) {
        std::string val = stripstr(token);
        if (!val.empty()) result.push_back(val);
    }
    return result;
}

/**
 * Parses a double-valued list like "[0.0, 1.5, 2.3]" into a vector<double>.
 * Used by concore.hpp's read/write which work with numeric data.
 */
inline std::vector<double> parselist_double(const std::string& str);

enum class ConcoreValueType { NUMBER, BOOL, STRING, ARRAY };

struct ConcoreValue {
    ConcoreValueType type;
    double   number;
    bool     boolean;
    std::string str;
    std::vector<ConcoreValue> array;

    ConcoreValue() : type(ConcoreValueType::NUMBER), number(0.0), boolean(false) {}

    static ConcoreValue make_number(double v) {
        ConcoreValue cv;
        cv.type   = ConcoreValueType::NUMBER;
        cv.number = v;
        return cv;
    }
    static ConcoreValue make_bool(bool v) {
        ConcoreValue cv;
        cv.type    = ConcoreValueType::BOOL;
        cv.boolean = v;
        cv.number  = v ? 1.0 : 0.0;
        return cv;
    }
    static ConcoreValue make_string(const std::string& v) {
        ConcoreValue cv;
        cv.type = ConcoreValueType::STRING;
        cv.str  = v;
        return cv;
    }
    static ConcoreValue make_array(const std::vector<ConcoreValue>& v) {
        ConcoreValue cv;
        cv.type  = ConcoreValueType::ARRAY;
        cv.array = v;
        return cv;
    }
};

inline void skip_ws(const std::string& s, size_t& pos) {
    while (pos < s.size() && std::isspace(static_cast<unsigned char>(s[pos])))
        ++pos;
}

inline ConcoreValue parse_literal_value(const std::string& s, size_t& pos);

inline ConcoreValue parse_literal_string(const std::string& s, size_t& pos) {
    char quote = s[pos];
    ++pos;
    std::string result;
    while (pos < s.size() && s[pos] != quote) {
        if (s[pos] == '\\' && pos + 1 < s.size()) {
            ++pos;
            switch (s[pos]) {
                case 'n':  result += '\n'; break;
                case 't':  result += '\t'; break;
                case '\\': result += '\\'; break;
                case '\'': result += '\''; break;
                case '"':  result += '"';  break;
                default:   result += '\\'; result += s[pos]; break;
            }
        } else {
            result += s[pos];
        }
        ++pos;
    }
    if (pos >= s.size())
        throw std::runtime_error("Invalid concore payload: unterminated string");
    ++pos;
    return ConcoreValue::make_string(result);
}

inline ConcoreValue parse_literal_array(const std::string& s, size_t& pos) {
    char open  = s[pos];
    char close = (open == '[') ? ']' : ')';
    ++pos;
    std::vector<ConcoreValue> elements;
    skip_ws(s, pos);
    if (pos < s.size() && s[pos] == close) { ++pos; return ConcoreValue::make_array(elements); }
    while (pos < s.size()) {
        elements.push_back(parse_literal_value(s, pos));
        skip_ws(s, pos);
        if (pos < s.size() && s[pos] == ',') { ++pos; skip_ws(s, pos); }
        if (pos < s.size() && s[pos] == close) { ++pos; return ConcoreValue::make_array(elements); }
    }
    throw std::runtime_error("Invalid concore payload: unterminated array/tuple");
}

inline ConcoreValue parse_literal_value(const std::string& s, size_t& pos) {
    skip_ws(s, pos);
    if (pos >= s.size())
        throw std::runtime_error("Invalid concore payload: unexpected end of input");

    char c = s[pos];

    if (c == '[' || c == '(')
        return parse_literal_array(s, pos);

    if (c == '\'' || c == '"')
        return parse_literal_string(s, pos);

    if (s.compare(pos, 4, "True") == 0 &&
        (pos + 4 >= s.size() ||
         (!std::isalnum(static_cast<unsigned char>(s[pos + 4])) && s[pos + 4] != '_'))) {
        pos += 4;
        return ConcoreValue::make_bool(true);
    }
    if (s.compare(pos, 5, "False") == 0 &&
        (pos + 5 >= s.size() ||
         (!std::isalnum(static_cast<unsigned char>(s[pos + 5])) && s[pos + 5] != '_'))) {
        pos += 5;
        return ConcoreValue::make_bool(false);
    }
    if (s.compare(pos, 4, "None") == 0 &&
        (pos + 4 >= s.size() ||
         (!std::isalnum(static_cast<unsigned char>(s[pos + 4])) && s[pos + 4] != '_'))) {
        pos += 4;
        return ConcoreValue::make_string("None");
    }

    {
        size_t start = pos;
        if (pos < s.size() && (s[pos] == '+' || s[pos] == '-')) ++pos;
        bool has_digits = false;
        while (pos < s.size() && std::isdigit(static_cast<unsigned char>(s[pos]))) {
            ++pos; has_digits = true;
        }
        if (pos < s.size() && s[pos] == '.') {
            ++pos;
            while (pos < s.size() && std::isdigit(static_cast<unsigned char>(s[pos]))) {
                ++pos; has_digits = true;
            }
        }
        if (has_digits && pos < s.size() && (s[pos] == 'e' || s[pos] == 'E')) {
            ++pos;
            if (pos < s.size() && (s[pos] == '+' || s[pos] == '-')) ++pos;
            while (pos < s.size() && std::isdigit(static_cast<unsigned char>(s[pos]))) ++pos;
        }
        if (has_digits && pos > start) {
            std::string numstr = s.substr(start, pos - start);
            try {
                double val = std::stod(numstr);
                return ConcoreValue::make_number(val);
            } catch (...) {
                throw std::runtime_error(
                    "Invalid concore payload: bad number '" + numstr + "'");
            }
        }
        pos = start;
    }

    throw std::runtime_error(
        std::string("Invalid concore payload: unsupported literal at position ") +
        std::to_string(pos));
}

inline ConcoreValue parse_literal(const std::string& s) {
    size_t pos = 0;
    ConcoreValue v = parse_literal_value(s, pos);
    skip_ws(s, pos);
    if (pos != s.size())
        throw std::runtime_error(
            "Invalid concore payload: unexpected trailing content");
    return v;
}

inline void flatten_numeric_impl(const ConcoreValue& v, std::vector<double>& out) {
    switch (v.type) {
        case ConcoreValueType::NUMBER:
            out.push_back(v.number);
            break;
        case ConcoreValueType::BOOL:
            out.push_back(v.boolean ? 1.0 : 0.0);
            break;
        case ConcoreValueType::STRING:
            break;
        case ConcoreValueType::ARRAY:
            for (const auto& elem : v.array)
                flatten_numeric_impl(elem, out);
            break;
    }
}

inline std::vector<double> flatten_numeric(const ConcoreValue& v) {
    std::vector<double> out;
    flatten_numeric_impl(v, out);
    return out;
}

inline std::vector<double> parselist_double(const std::string& str) {
    std::string trimmed = stripstr(str);
    if (trimmed.empty()) return {};
    try {
        ConcoreValue v = parse_literal(trimmed);
        return flatten_numeric(v);
    } catch (...) {
        std::vector<double> result;
        if (trimmed.size() < 2) return result;
        if (trimmed.front() == '[' || trimmed.front() == '(') {
            std::vector<std::string> tokens = parselist(trimmed);
            for (const auto& tok : tokens) {
                try { result.push_back(std::stod(tok)); } catch (...) {}
            }
        }
        return result;
    }
}

/**
 * Reads a file and parses its content as a dict.
 * Returns defaultValue on any failure (matches Python safe_literal_eval).
 */
inline std::map<std::string, std::string> safe_literal_eval_dict(
    const std::string& filename,
    const std::map<std::string, std::string>& defaultValue)
{
    std::ifstream file(filename);
    if (!file) return defaultValue;
    std::stringstream buf;
    buf << file.rdbuf();
    std::string content = buf.str();
    try {
        return parsedict(content);
    } catch (...) {
        return defaultValue;
    }
}

/**
 * Loads simulation parameters from a concore.params file.
 * Handles Windows quote wrapping, semicolon-separated key=value,
 * and dict-literal format.
 */
inline std::map<std::string, std::string> load_params(const std::string& params_file) {
    std::ifstream file(params_file);
    if (!file) return {};
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string sparams = buffer.str();

    // Windows sometimes keeps surrounding quotes
    if (!sparams.empty() && sparams[0] == '"') {
        size_t closing = sparams.find('"', 1);
        if (closing != std::string::npos)
            sparams = sparams.substr(1, closing - 1);
    }

    sparams = stripstr(sparams);
    if (sparams.empty()) return {};

    // If already a dict literal, parse directly
    if (sparams.front() == '{') {
        try { return parsedict(sparams); } catch (...) {}
    }

    // Otherwise convert semicolon-separated key=value to dict format
    // e.g. "a=1;b=2" -> {"a":"1","b":"2"}
    std::string normalized = std::regex_replace(sparams, std::regex(";"), ",");
    std::string converted = "{\"" +
        std::regex_replace(
            std::regex_replace(
                std::regex_replace(normalized, std::regex(","), ",\""),
                std::regex("="), "\":"),
            std::regex(" "), "") +
        "}";
    try { return parsedict(converted); } catch (...) {}

    return {};
}

/**
 * Reads maxtime from concore.maxtime file, falls back to defaultValue.
 */
inline double load_maxtime(const std::string& maxtime_file, double defaultValue) {
    std::ifstream file(maxtime_file);
    if (!file) return defaultValue;
    double val;
    if (file >> val) return val;
    return defaultValue;
}

/**
 * Returns param value by name, or default if not found.
 */
inline std::string tryparam(
    const std::map<std::string, std::string>& params,
    const std::string& name,
    const std::string& defaultValue)
{
    auto it = params.find(name);
    return (it != params.end()) ? it->second : defaultValue;
}


// ===================================================================
// ZeroMQ Transport (opt-in: compile with -DCONCORE_USE_ZMQ)
// ===================================================================
#ifdef CONCORE_USE_ZMQ
#include <zmq.hpp>

/**
 * ZMQ socket wrapper with bind/connect, timeouts, and retry.
 */
class ZeroMQPort {
public:
    zmq::context_t context;
    zmq::socket_t  socket;
    std::string    port_type;
    std::string    address;

    ZeroMQPort(const std::string& port_type_, const std::string& address_, int socket_type)
        : context(1), socket(context, socket_type),
          port_type(port_type_), address(address_)
    {
        socket.setsockopt(ZMQ_RCVTIMEO, 2000);
        socket.setsockopt(ZMQ_SNDTIMEO, 2000);
        socket.setsockopt(ZMQ_LINGER,   0);

        if (port_type == "bind")
            socket.bind(address);
        else
            socket.connect(address);
    }

    ZeroMQPort(const ZeroMQPort&) = delete;
    ZeroMQPort& operator=(const ZeroMQPort&) = delete;

    /**
     * Sends a vector<double> as "[v0, v1, ...]" with retry on timeout.
     */
    void send_with_retry(const std::vector<double>& payload) {
        std::ostringstream ss;
        ss << "[";
        for (size_t i = 0; i < payload.size(); ++i) {
            if (i) ss << ", ";
            ss << payload[i];
        }
        ss << "]";
        std::string msg = ss.str();
        for (int attempt = 0; attempt < 5; ++attempt) {
            try {
                zmq::message_t zmsg(msg.begin(), msg.end());
                socket.send(zmsg, zmq::send_flags::none);
                return;
            } catch (const zmq::error_t&) {
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            }
        }
        std::cerr << "ZMQ send failed after retries." << std::endl;
    }

    /**
     * Sends a raw string with retry on timeout.
     */
    void send_string_with_retry(const std::string& msg) {
        for (int attempt = 0; attempt < 5; ++attempt) {
            try {
                zmq::message_t zmsg(msg.begin(), msg.end());
                socket.send(zmsg, zmq::send_flags::none);
                return;
            } catch (const zmq::error_t&) {
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            }
        }
        std::cerr << "ZMQ send failed after retries." << std::endl;
    }

    /**
     * Receives and parses "[v0, v1, ...]" back to vector<double>.
     */
    std::vector<double> recv_with_retry() {
        for (int attempt = 0; attempt < 5; ++attempt) {
            try {
                zmq::message_t zmsg;
                auto res = socket.recv(zmsg, zmq::recv_flags::none);
                if (res) {
                    std::string data(static_cast<char*>(zmsg.data()), zmsg.size());
                    return parselist_double(data);
                }
            } catch (const zmq::error_t&) {
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            }
        }
        std::cerr << "ZMQ recv failed after retries." << std::endl;
        return {};
    }
};

/**
 * Maps socket type string ("REQ", "REP", etc.) to ZMQ constant.
 * Returns -1 on unknown type.
 */
inline int zmq_socket_type_from_string(const std::string& s) {
    if (s == "REQ")  return ZMQ_REQ;
    if (s == "REP")  return ZMQ_REP;
    if (s == "PUB")  return ZMQ_PUB;
    if (s == "SUB")  return ZMQ_SUB;
    if (s == "PUSH") return ZMQ_PUSH;
    if (s == "PULL") return ZMQ_PULL;
    if (s == "PAIR") return ZMQ_PAIR;
    return -1;
}
#endif // CONCORE_USE_ZMQ

} // namespace concore_base

#endif // CONCORE_BASE_HPP
