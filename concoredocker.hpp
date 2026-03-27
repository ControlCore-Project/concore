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
#include <map>
#include <cstring>

#ifdef __linux__
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#endif

#include "concore_base.hpp"

class Concore {
private:
    static constexpr size_t SHM_SIZE = 4096;

    int shmId_create = -1;
    int shmId_get = -1;
    char* sharedData_create = nullptr;
    char* sharedData_get = nullptr;
    int communication_iport = 0;  // iport refers to input port
    int communication_oport = 0;  // oport refers to output port

public:
    enum class ReadStatus {
        SUCCESS,
        TIMEOUT,
        PARSE_ERROR,
        FILE_NOT_FOUND,
        RETRIES_EXCEEDED
    };

    struct ReadResult {
        ReadStatus status;
        std::vector<double> data;
    };

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
    ReadStatus last_read_status = ReadStatus::SUCCESS;
#ifdef CONCORE_USE_ZMQ
    std::map<std::string, concore_base::ZeroMQPort*> zmq_ports;
#endif

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

#ifdef __linux__
        int iport_number = -1;
        int oport_number = -1;

        if (!iport.empty())
            iport_number = ExtractNumeric(iport.begin()->first);
        if (!oport.empty())
            oport_number = ExtractNumeric(oport.begin()->first);

        if (oport_number != -1) {
            communication_oport = 1;
            createSharedMemory(oport_number);
        }
        if (iport_number != -1) {
            communication_iport = 1;
            getSharedMemory(iport_number);
        }
#endif
    }

    ~Concore() {
#ifdef CONCORE_USE_ZMQ
        for (auto& kv : zmq_ports)
            delete kv.second;
        zmq_ports.clear();
#endif
#ifdef __linux__
        if (communication_oport == 1 && sharedData_create != nullptr)
            shmdt(sharedData_create);
        if (communication_iport == 1 && sharedData_get != nullptr)
            shmdt(sharedData_get);
        if (shmId_create != -1)
            shmctl(shmId_create, IPC_RMID, nullptr);
#endif
    }

    Concore(const Concore&) = delete;
    Concore& operator=(const Concore&) = delete;

    Concore(Concore&& other) noexcept
        : iport(std::move(other.iport)), oport(std::move(other.oport)),
          s(std::move(other.s)), olds(std::move(other.olds)),
          delay(other.delay), retrycount(other.retrycount),
          inpath(std::move(other.inpath)), outpath(std::move(other.outpath)),
          simtime(other.simtime), maxtime(other.maxtime),
          params(std::move(other.params)),
          shmId_create(other.shmId_create), shmId_get(other.shmId_get),
          sharedData_create(other.sharedData_create), sharedData_get(other.sharedData_get),
          communication_iport(other.communication_iport), communication_oport(other.communication_oport)
    {
#ifdef CONCORE_USE_ZMQ
        zmq_ports = std::move(other.zmq_ports);
#endif
        other.shmId_create = -1;
        other.shmId_get = -1;
        other.sharedData_create = nullptr;
        other.sharedData_get = nullptr;
        other.communication_iport = 0;
        other.communication_oport = 0;
    }

    Concore& operator=(Concore&& other) noexcept
    {
        if (this == &other)
            return *this;

#ifdef CONCORE_USE_ZMQ
        for (auto& kv : zmq_ports)
            delete kv.second;
        zmq_ports = std::move(other.zmq_ports);
#endif
#ifdef __linux__
        if (communication_oport == 1 && sharedData_create != nullptr)
            shmdt(sharedData_create);
        if (communication_iport == 1 && sharedData_get != nullptr)
            shmdt(sharedData_get);
        if (shmId_create != -1)
            shmctl(shmId_create, IPC_RMID, nullptr);
#endif

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
        shmId_create = other.shmId_create;
        shmId_get = other.shmId_get;
        sharedData_create = other.sharedData_create;
        sharedData_get = other.sharedData_get;
        communication_iport = other.communication_iport;
        communication_oport = other.communication_oport;

        other.shmId_create = -1;
        other.shmId_get = -1;
        other.sharedData_create = nullptr;
        other.sharedData_get = nullptr;
        other.communication_iport = 0;
        other.communication_oport = 0;

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

    key_t ExtractNumeric(const std::string& str) {
        std::string numberString;
        size_t numDigits = 0;
        while (numDigits < str.length() && std::isdigit(str[numDigits])) {
            numberString += str[numDigits];
            ++numDigits;
        }
        if (numDigits == 0)
            return -1;
        if (numDigits == 1 && std::stoi(numberString) <= 0)
            return -1;
        return std::stoi(numberString);
    }

#ifdef __linux__
    void createSharedMemory(key_t key) {
        shmId_create = shmget(key, SHM_SIZE, IPC_CREAT | 0666);
        if (shmId_create == -1) {
            std::cerr << "Failed to create shared memory segment.\n";
            return;
        }
        sharedData_create = static_cast<char*>(shmat(shmId_create, NULL, 0));
        if (sharedData_create == reinterpret_cast<char*>(-1)) {
            std::cerr << "Failed to attach shared memory segment.\n";
            sharedData_create = nullptr;
        }
    }

    void getSharedMemory(key_t key) {
        int retry = 0;
        const int MAX_RETRY = 100;
        while (retry < MAX_RETRY) {
            shmId_get = shmget(key, SHM_SIZE, 0666);
            if (shmId_get != -1)
                break;
            std::cout << "Shared memory does not exist. Make sure the writer process is running.\n";
            sleep(1);
            retry++;
        }
        if (shmId_get == -1) {
            std::cerr << "Failed to get shared memory segment after max retries.\n";
            return;
        }
        sharedData_get = static_cast<char*>(shmat(shmId_get, NULL, 0));
        if (sharedData_get == reinterpret_cast<char*>(-1)) {
            std::cerr << "Failed to attach shared memory segment.\n";
            sharedData_get = nullptr;
        }
    }
#endif

    bool unchanged() {
        if (olds == s) {
            s.clear();
            return true;
        }
        olds = s;
        return false;
    }

    std::vector<double> read(int port, const std::string& name, const std::string& initstr) {
#ifdef __linux__
        if (communication_iport == 1)
            return read_SM(port, name, initstr);
#endif
        ReadStatus status = ReadStatus::SUCCESS;
        std::this_thread::sleep_for(std::chrono::seconds(delay));
        std::string file_path = inpath + "/" + std::to_string(port) + "/" + name;
        std::ifstream infile(file_path);
        std::string ins;

        if (!infile) {
            std::cerr << "File " << file_path << " not found, using default value.\n";
            status = ReadStatus::FILE_NOT_FOUND;
            std::vector<double> fallback = concore_base::parselist_double(initstr);
            last_read_status = status;
            return fallback;
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
            status = ReadStatus::RETRIES_EXCEEDED;
            std::vector<double> fallback = concore_base::parselist_double(initstr);
            last_read_status = status;
            return fallback;
        }

        s += ins;
        std::vector<double> inval = concore_base::parselist_double(ins);
        if (inval.empty()) {
            status = ReadStatus::PARSE_ERROR;
            inval = concore_base::parselist_double(initstr);
        }
        if (inval.empty()) {
            last_read_status = status;
            return inval;
        }
        last_read_status = status;
        simtime = simtime > inval[0] ? simtime : inval[0];
        inval.erase(inval.begin());
        return inval;
    }

    ReadResult read_result(int port, const std::string& name, const std::string& initstr) {
        ReadResult result;
        result.data = read(port, name, initstr);
        result.status = last_read_status;
        return result;
    }

#ifdef __linux__
    std::vector<double> read_SM(int port, const std::string& name, const std::string& initstr) {
        ReadStatus status = ReadStatus::SUCCESS;
        std::this_thread::sleep_for(std::chrono::seconds(delay));
        std::string ins;
        try {
            if (shmId_get != -1 && sharedData_get && sharedData_get[0] != '\0')
                ins = std::string(sharedData_get, strnlen(sharedData_get, SHM_SIZE));
            else
                throw 505;
        } catch (...) {
            status = ReadStatus::FILE_NOT_FOUND;
            ins = initstr;
        }

        int retry = 0;
        const int MAX_RETRY = 100;
        while ((int)ins.length() == 0 && retry < MAX_RETRY) {
            std::this_thread::sleep_for(std::chrono::seconds(delay));
            try {
                if (shmId_get != -1 && sharedData_get) {
                    ins = std::string(sharedData_get, strnlen(sharedData_get, SHM_SIZE));
                    retrycount++;
                } else {
                    retrycount++;
                    throw 505;
                }
            } catch (...) {
                std::cerr << "Read error\n";
            }
            retry++;
        }
        if ((int)ins.length() == 0)
            status = ReadStatus::RETRIES_EXCEEDED;

        s += ins;
        std::vector<double> inval = concore_base::parselist_double(ins);
        if (inval.empty()) {
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::PARSE_ERROR;
            inval = concore_base::parselist_double(initstr);
        }
        if (inval.empty()) {
            last_read_status = status;
            return inval;
        }
        last_read_status = status;
        simtime = simtime > inval[0] ? simtime : inval[0];
        inval.erase(inval.begin());
        return inval;
    }
#endif

    void write(int port, const std::string& name, const std::vector<double>& val, int delta = 0) {
#ifdef __linux__
        if (communication_oport == 1) {
            write_SM(port, name, val, delta);
            return;
        }
#endif
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

#ifdef __linux__
    void write_SM(int port, const std::string& name, std::vector<double> val, int delta = 0) {
        try {
            if (shmId_create == -1)
                throw 505;
            val.insert(val.begin(), simtime + delta);
            std::ostringstream outfile;
            outfile << '[';
            for (size_t i = 0; i < val.size() - 1; i++)
                outfile << val[i] << ',';
            outfile << val[val.size() - 1] << ']';
            std::string result = outfile.str();
            if (result.size() >= SHM_SIZE) {
                std::cerr << "ERROR: write_SM payload (" << result.size()
                          << " bytes) exceeds " << SHM_SIZE - 1
                          << "-byte shared memory limit. Data truncated!" << std::endl;
            }
            std::strncpy(sharedData_create, result.c_str(), SHM_SIZE - 1);
            sharedData_create[SHM_SIZE - 1] = '\0';
        } catch (...) {
            std::cerr << "skipping +" << outpath << port << "/" << name << "\n";
        }
    }
#endif

#ifdef CONCORE_USE_ZMQ
    void init_zmq_port(const std::string& port_name, const std::string& port_type,
                       const std::string& address, const std::string& socket_type_str) {
        if (zmq_ports.count(port_name)) return;
        int sock_type = concore_base::zmq_socket_type_from_string(socket_type_str);
        if (sock_type == -1) {
            std::cerr << "init_zmq_port: unknown socket type '" << socket_type_str << "'\n";
            return;
        }
        zmq_ports[port_name] = new concore_base::ZeroMQPort(port_type, address, sock_type);
    }

    std::vector<double> read_ZMQ(const std::string& port_name, const std::string& name, const std::string& initstr) {
        ReadStatus status = ReadStatus::SUCCESS;
        auto it = zmq_ports.find(port_name);
        if (it == zmq_ports.end()) {
            std::cerr << "read_ZMQ: port '" << port_name << "' not initialized\n";
            status = ReadStatus::FILE_NOT_FOUND;
            last_read_status = status;
            return concore_base::parselist_double(initstr);
        }
        std::vector<double> inval = it->second->recv_with_retry();
        if (inval.empty()) {
            status = ReadStatus::TIMEOUT;
            inval = concore_base::parselist_double(initstr);
        }
        if (inval.empty()) {
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::PARSE_ERROR;
            last_read_status = status;
            return inval;
        }
        last_read_status = status;
        simtime = simtime > inval[0] ? simtime : inval[0];
        s += port_name;
        inval.erase(inval.begin());
        return inval;
    }

    void write_ZMQ(const std::string& port_name, const std::string& name, std::vector<double> val, int delta = 0) {
        auto it = zmq_ports.find(port_name);
        if (it == zmq_ports.end()) {
            std::cerr << "write_ZMQ: port '" << port_name << "' not initialized\n";
            return;
        }
        val.insert(val.begin(), simtime + delta);
        it->second->send_with_retry(val);
        // simtime must not be mutated here.
    }

    std::vector<double> read(const std::string& port_name, const std::string& name, const std::string& initstr) {
        return read_ZMQ(port_name, name, initstr);
    }

    ReadResult read_result(const std::string& port_name, const std::string& name, const std::string& initstr) {
        ReadResult result;
        result.data = read(port_name, name, initstr);
        result.status = last_read_status;
        return result;
    }

    void write(const std::string& port_name, const std::string& name, std::vector<double> val, int delta = 0) {
        return write_ZMQ(port_name, name, val, delta);
    }
#endif // CONCORE_USE_ZMQ

    std::vector<double> initval(const std::string& simtime_val) {
        std::vector<double> val = concore_base::parselist_double(simtime_val);
        if (val.empty()) return val;
        simtime = val[0];
        val.erase(val.begin());
        return val;
    }
};

#endif // CONCOREDOCKER_HPP
