#ifndef CONCORE_HPP
#define CONCORE_HPP

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <chrono>
#include <thread>
#include <filesystem>
#include <stdexcept>
#include <algorithm>

class Concore {
public:
    std::unordered_map<std::string, std::string> iport;
    std::unordered_map<std::string, std::string> oport;
    std::string s, olds;
    int delay = 1;
    int retrycount = 0;
    std::string inpath = "/in";
    std::string outpath = "/out";
    int simtime = 0;
    int maxtime = 100;
    std::unordered_map<std::string, std::string> params;

    std::string stripstr(const std::string& str) {
        size_t start = str.find_first_not_of(" \t\n\r");
        if (start == std::string::npos) return "";
        size_t end = str.find_last_not_of(" \t\n\r");
        return str.substr(start, end - start + 1);
    }

    std::string stripquotes(const std::string& str) {
        if (str.size() >= 2 && ((str.front() == '\'' && str.back() == '\'') || (str.front() == '"' && str.back() == '"')))
            return str.substr(1, str.size() - 2);
        return str;
    }

    std::vector<std::string> split_toplevel(const std::string& s) {
        std::vector<std::string> tokens;
        int depth = 0;
        bool in_sq = false, in_dq = false;
        std::string cur;
        for (size_t i = 0; i < s.size(); i++) {
            char c = s[i];
            if (in_sq) {
                cur += c;
                if (c == '\\' && i + 1 < s.size()) { cur += s[++i]; continue; }
                if (c == '\'') in_sq = false;
                continue;
            }
            if (in_dq) {
                cur += c;
                if (c == '\\' && i + 1 < s.size()) { cur += s[++i]; continue; }
                if (c == '"') in_dq = false;
                continue;
            }
            if (c == '\'') { in_sq = true; cur += c; continue; }
            if (c == '"')  { in_dq = true; cur += c; continue; }
            if (c == '[' || c == '{' || c == '(') { depth++; cur += c; continue; }
            if (c == ']' || c == '}' || c == ')') { depth--; cur += c; continue; }
            if (c == ',' && depth == 0) {
                tokens.push_back(cur);
                cur.clear();
                continue;
            }
            cur += c;
        }
        if (!cur.empty() || !tokens.empty()) tokens.push_back(cur);
        return tokens;
    }

    std::unordered_map<std::string, std::string> parsedict(const std::string& str) {
        std::unordered_map<std::string, std::string> result;
        std::string trimmed = stripstr(str);
        if (trimmed.size() < 2 || trimmed.front() != '{' || trimmed.back() != '}')
            return result;
        std::string inner = trimmed.substr(1, trimmed.size() - 2);
        if (stripstr(inner).empty()) return result;
        for (auto& item : split_toplevel(inner)) {
            // find first colon not inside quotes
            size_t colon = std::string::npos;
            bool sq = false, dq = false;
            for (size_t i = 0; i < item.size(); i++) {
                char c = item[i];
                if (sq) { if (c == '\\' && i+1 < item.size()) i++; else if (c == '\'') sq = false; continue; }
                if (dq) { if (c == '\\' && i+1 < item.size()) i++; else if (c == '"') dq = false; continue; }
                if (c == '\'') { sq = true; continue; }
                if (c == '"') { dq = true; continue; }
                if (c == ':') { colon = i; break; }
            }
            if (colon == std::string::npos) continue;
            std::string key = stripquotes(stripstr(item.substr(0, colon)));
            std::string val = stripquotes(stripstr(item.substr(colon + 1)));
            if (!key.empty()) result[key] = val;
        }
        return result;
    }

    std::vector<std::string> parselist(const std::string& str) {
        std::vector<std::string> result;
        std::string trimmed = stripstr(str);
        if (trimmed.size() < 2 || trimmed.front() != '[' || trimmed.back() != ']')
            return result;
        std::string inner = trimmed.substr(1, trimmed.size() - 2);
        for (auto& item : split_toplevel(inner)) {
            std::string val = stripstr(item);
            if (!val.empty()) result.push_back(val);
        }
        return result;
    }

    Concore() {
        iport = safe_literal_eval("concore.iport", {});
        oport = safe_literal_eval("concore.oport", {});
        default_maxtime(100);
        load_params();
    }

    std::unordered_map<std::string, std::string> safe_literal_eval(const std::string& filename, std::unordered_map<std::string, std::string> defaultValue) {
        std::ifstream file(filename);
        if (!file) {
            std::cerr << "Error reading " << filename << "\n";
            return defaultValue;
        }
        std::stringstream buf;
        buf << file.rdbuf();
        std::string content = buf.str();
        try {
            return parsedict(content);
        } catch (...) {
            return defaultValue;
        }
    }

    void load_params() {
        std::ifstream file(inpath + "/1/concore.params");
        if (!file) return;
        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string sparams = stripstr(buffer.str());

        if (sparams.size() >= 2 && sparams.front() == '"' && sparams.back() == '"')
            sparams = sparams.substr(1, sparams.size() - 2);

        if (sparams.empty()) return;

        if (sparams.front() == '{' && sparams.back() == '}') {
            params = parsedict(sparams);
            return;
        }

        std::stringstream ss(sparams);
        std::string item;
        while (std::getline(ss, item, ';')) {
            size_t eq = item.find('=');
            if (eq == std::string::npos) continue;
            std::string key = stripstr(item.substr(0, eq));
            std::string val = stripstr(item.substr(eq + 1));
            if (!key.empty()) params[key] = val;
        }
    }

    std::string tryparam(const std::string& n, const std::string& i) {
        return params.count(n) ? params[n] : i;
    }

    void default_maxtime(int defaultValue) {
        maxtime = defaultValue;
        std::ifstream file(inpath + "/1/concore.maxtime");
        if (file) {
            file >> maxtime;
        }
    }

    bool unchanged() {
        if (olds == s) {
            s.clear();
            return true;
        }
        olds = s;
        return false;
    }

    std::vector<std::string> read(int port, const std::string& name, const std::string& initstr) {
        std::this_thread::sleep_for(std::chrono::seconds(delay));
        std::string file_path = inpath + std::to_string(port) + "/" + name;
        std::ifstream infile(file_path);
        std::string ins;

        if (!infile) {
            std::cerr << "File " << file_path << " not found, using default value.\n";
            return {initstr};
        }
        std::getline(infile, ins);
        
        int attempts = 0, max_retries = 5;
        while (ins.empty() && attempts < max_retries) {
            std::this_thread::sleep_for(std::chrono::seconds(delay));
            infile.open(file_path);
            if (infile) std::getline(infile, ins);
            attempts++;
            retrycount++;
        }

        if (ins.empty()) {
            std::cerr << "Max retries reached for " << file_path << ", using default value.\n";
            return {initstr};
        }
        
        s += ins;
        try {
            std::vector<std::string> inval = parselist(ins);
            if (!inval.empty()) {
                int file_simtime = (int)std::stod(inval[0]);
                simtime = std::max(simtime, file_simtime);
                return std::vector<std::string>(inval.begin() + 1, inval.end());
            }
        } catch (...) {}
        return {ins};
    }

    void write(int port, const std::string& name, const std::vector<std::string>& val, int delta = 0) {
        std::string file_path = outpath + std::to_string(port) + "/" + name;
        std::ofstream outfile(file_path);
        if (!outfile) {
            std::cerr << "Error writing to " << file_path << "\n";
            return;
        }
        if (!val.empty()) {
            outfile << "[" << simtime + delta << ", ";
            for (size_t i = 0; i < val.size(); ++i) {
                outfile << val[i] << (i + 1 < val.size() ? ", " : "");
            }
            outfile << "]";
            simtime += delta;
        }
    }

    std::vector<std::string> initval(const std::string& simtime_val) {
        try {
            std::vector<std::string> val = parselist(simtime_val);
            if (!val.empty()) {
                simtime = (int)std::stod(val[0]);
                return std::vector<std::string>(val.begin() + 1, val.end());
            }
        } catch (...) {}
        return {};
    }
};

#endif
