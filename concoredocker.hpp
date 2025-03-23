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
#include <regex>

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
        return defaultValue;
    }

    void load_params() {
        std::ifstream file(inpath + "/1/concore.params");
        if (!file) return;
        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string sparams = buffer.str();

        if (!sparams.empty() && sparams[0] == '"') {
            sparams = sparams.substr(1, sparams.find('"') - 1);
        }

        if (!sparams.empty() && sparams[0] != '{') {
            sparams = "{'" + std::regex_replace(std::regex_replace(std::regex_replace(sparams, std::regex(","), ", '"), std::regex("="), "':"), std::regex(" "), "") + "}";
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
};

#endif
