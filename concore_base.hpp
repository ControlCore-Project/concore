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
inline std::vector<double> parselist_double(const std::string& str) {
    std::vector<double> result;
    std::vector<std::string> tokens = parselist(str);
    for (const auto& tok : tokens) {
        result.push_back(std::stod(tok));
    }
    return result;
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
    std::string converted = "{\"" +
        std::regex_replace(
            std::regex_replace(
                std::regex_replace(sparams, std::regex(","), ",\""),
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

} // namespace concore_base

#endif // CONCORE_BASE_HPP
