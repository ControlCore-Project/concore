#ifndef CONCOREDOCKER_HPP
#define CONCOREDOCKER_HPP

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
#include <regex>
#include <algorithm>

#include "concore_base.hpp"

class Concore {
public:
    std::unordered_map<std::string, std::string> iport;
    std::unordered_map<std::string, std::string> oport;
    std::string s, olds;
    int delay = 1;
    int retrycount = 0;
    std::string inpath = "/in";
    std::string outpath = "/out";
    double simtime = 0;
    double maxtime = 100;
    std::unordered_map<std::string, std::string> params;

    std::string stripstr(const std::string& str) {
        return concore_base::stripstr(str);
    }

    std::string stripquotes(const std::string& str) {
        return concore_base::stripquotes(str);
    }

    std::unordered_map<std::string, std::string> parsedict(const std::string& str) {
        auto ordered = concore_base::parsedict(str);
        return std::unordered_map<std::string, std::string>(ordered.begin(), ordered.end());
    }

    std::vector<std::string> parselist(const std::string& str) {
        return concore_base::parselist(str);
    }

    Concore() {
        iport = safe_literal_eval("concore.iport", {});
        oport = safe_literal_eval("concore.oport", {});
        default_maxtime(100);
        load_params();
    }

    Concore(const Concore&) = delete;
    Concore& operator=(const Concore&) = delete;

    Concore(Concore&& other) noexcept
        : iport(std::move(other.iport)), oport(std::move(other.oport)),
          s(std::move(other.s)), olds(std::move(other.olds)),
          delay(other.delay), retrycount(other.retrycount),
          inpath(std::move(other.inpath)), outpath(std::move(other.outpath)),
          simtime(other.simtime), maxtime(other.maxtime),
          params(std::move(other.params))
    {}

    Concore& operator=(Concore&& other) noexcept
    {
        if (this == &other)
            return *this;

        iport = std::move(other.iport);
        oport = std::move(other.oport);
        s = std::move(other.s);
        olds = std::move(other.olds);
        delay = other.delay;
        retrycount = other.retrycount;
        inpath = std::move(other.inpath);
        outpath = std::move(other.outpath);
        simtime = other.simtime;
        maxtime = other.maxtime;
        params = std::move(other.params);

        return *this;
    }

    std::unordered_map<std::string, std::string> safe_literal_eval(const std::string& filename, std::unordered_map<std::string, std::string> defaultValue) {
        std::ifstream file(filename);
        if (!file) return defaultValue;
        std::stringstream buf;
        buf << file.rdbuf();
        auto result = concore_base::parsedict(buf.str());
        if (result.empty()) return defaultValue;
        return std::unordered_map<std::string, std::string>(result.begin(), result.end());
    }

    void load_params() {
        auto ordered = concore_base::load_params(inpath + "/1/concore.params");
        params = std::unordered_map<std::string, std::string>(ordered.begin(), ordered.end());
    }

    std::string tryparam(const std::string& n, const std::string& i) {
        return params.count(n) ? params[n] : i;
    }

    void default_maxtime(double defaultValue) {
        maxtime = concore_base::load_maxtime(
            inpath + "/1/concore.maxtime", defaultValue);
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
        std::string file_path = inpath + "/" + std::to_string(port) + "/" + name;
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
            infile.close();
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
                double file_simtime = std::stod(inval[0]);
                simtime = std::max(simtime, file_simtime);
                return std::vector<std::string>(inval.begin() + 1, inval.end());
            }
        } catch (...) {}
        return {ins};
    }

    void write(int port, const std::string& name, const std::vector<std::string>& val, int delta = 0) {
        std::string file_path = outpath + "/" + std::to_string(port) + "/" + name;
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
            // simtime must not be mutated here (issue #385).
        }
    }

    std::vector<std::string> initval(const std::string& simtime_val) {
        try {
            std::vector<std::string> val = parselist(simtime_val);
            if (!val.empty()) {
                simtime = std::stod(val[0]);
                return std::vector<std::string>(val.begin() + 1, val.end());
            }
        } catch (...) {}
        return {};
    }
};

#endif // CONCOREDOCKER_HPP
