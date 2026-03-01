// concore.hpp -- this C++ include file will be the equivalent of concore.py
#ifndef CONCORE_HPP
#define CONCORE_HPP

#include <iostream>
#include <vector>
#include <iomanip> //for setprecision
#include <map>

//libraries for files
#include <fstream>
#include <sstream>
#include <string>

//libraries for platform independent delay. Supports C++11 upwards
#include <chrono>
#include <thread>
#ifdef __linux__
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#endif
#include <cstring>
#include <cctype>
#include <regex>

#include "concore_base.hpp"

using namespace std;

/**
 * @class Concore
 * @brief Class representing the Concore implementation in C++
 */
class Concore{

private:
    //private variables
    string s="",olds="";
    string inpath = "./in";
    string outpath = "./out";

    int shmId_create = -1;
    int shmId_get = -1;

    char* sharedData_create = nullptr;
    char* sharedData_get = nullptr;
    // File sharing:- 0, Shared Memory:- 1
    int communication_iport = 0;  // iport refers to input port
    int communication_oport = 0;  // oport refers to input port

#ifdef CONCORE_USE_ZMQ
    map<string, concore_base::ZeroMQPort*> zmq_ports;
#endif

 public:
    double delay = 1;
    int retrycount = 0;
    double simtime;
    int maxtime = 100;
    map <string, int> iport;
    map <string, int> oport;
    map <string, string> params;

    /**
     * @brief Constructor for Concore class.
     *        Initializes the iport and oport maps by parsing the respective files.
     *        It also creates or attaches to the shared memory segment if required.
     */
    Concore(){
        iport = mapParser("concore.iport");
        oport = mapParser("concore.oport");
        default_maxtime(100);
        load_params();   
        
        int iport_number = -1;
        int oport_number = -1;
        
        if (!iport.empty()) {
            std::map<std::string, int>::iterator it_iport = iport.begin();
            iport_number = ExtractNumeric(it_iport->first);
        }
        if (!oport.empty()) {
            std::map<std::string, int>::iterator it_oport = oport.begin();
            oport_number = ExtractNumeric(it_oport->first);
        }

        // if iport_number and oport_number is equal to -1 then it refers to File Method, 
        // otherwise it refers to Shared Memory and the number represent the unique key.

#ifdef __linux__
        if(oport_number != -1)
        {
            // oport_number is not equal to -1 so refers to SM and value is key.
            communication_oport = 1;
            this->createSharedMemory(oport_number);
        }  

        if(iport_number != -1)
        {
            // iport_number is not equal to -1 so refers to SM and value is key.
            communication_iport = 1;
            this->getSharedMemory(iport_number);
        }
#endif
    }

    /**
     * @brief Destructor for Concore class.
     *        Detaches and removes the shared memory segment if shared memory created.
     */
    ~Concore()
    {
#ifdef CONCORE_USE_ZMQ
        for (auto& kv : zmq_ports)
            delete kv.second;
        zmq_ports.clear();
#endif
#ifdef __linux__
        // Detach the shared memory segment from the process
        if (communication_oport == 1 && sharedData_create != nullptr) {
            shmdt(sharedData_create);
        }
        if (communication_iport == 1 && sharedData_get != nullptr) {
            shmdt(sharedData_get);
        }

        // Remove the shared memory segment
        if (shmId_create != -1) {
            shmctl(shmId_create, IPC_RMID, nullptr);
        }
#endif
    }

    /**
     * @brief Concore is not copyable as it owns shared memory handles.
     */
    Concore(const Concore&) = delete;
    Concore& operator=(const Concore&) = delete;

    /**
     * @brief Move constructor. Transfers SHM handle ownership to the new instance.
     */
    Concore(Concore&& other) noexcept
        : s(std::move(other.s)), olds(std::move(other.olds)),
          inpath(std::move(other.inpath)), outpath(std::move(other.outpath)),
          shmId_create(other.shmId_create), shmId_get(other.shmId_get),
          sharedData_create(other.sharedData_create), sharedData_get(other.sharedData_get),
          communication_iport(other.communication_iport), communication_oport(other.communication_oport),
          delay(other.delay), retrycount(other.retrycount), simtime(other.simtime),
          maxtime(other.maxtime), iport(std::move(other.iport)), oport(std::move(other.oport)),
          params(std::move(other.params))
    {
        other.shmId_create = -1;
        other.shmId_get = -1;
        other.sharedData_create = nullptr;
        other.sharedData_get = nullptr;
        other.communication_iport = 0;
        other.communication_oport = 0;
    }

    /**
     * @brief Move assignment. Cleans up current SHM resources, then takes ownership from other.
     */
    Concore& operator=(Concore&& other) noexcept
    {
        if (this == &other)
            return *this;

#ifdef __linux__
        if (communication_oport == 1 && sharedData_create != nullptr)
            shmdt(sharedData_create);
        if (communication_iport == 1 && sharedData_get != nullptr)
            shmdt(sharedData_get);
        if (shmId_create != -1)
            shmctl(shmId_create, IPC_RMID, nullptr);
#endif

        s = std::move(other.s);
        olds = std::move(other.olds);
        inpath = std::move(other.inpath);
        outpath = std::move(other.outpath);
        shmId_create = other.shmId_create;
        shmId_get = other.shmId_get;
        sharedData_create = other.sharedData_create;
        sharedData_get = other.sharedData_get;
        communication_iport = other.communication_iport;
        communication_oport = other.communication_oport;
        delay = other.delay;
        retrycount = other.retrycount;
        simtime = other.simtime;
        maxtime = other.maxtime;
        iport = std::move(other.iport);
        oport = std::move(other.oport);
        params = std::move(other.params);

        other.shmId_create = -1;
        other.shmId_get = -1;
        other.sharedData_create = nullptr;
        other.sharedData_get = nullptr;
        other.communication_iport = 0;
        other.communication_oport = 0;

        return *this;
    }

    /**
     * @brief Extracts the numeric part from a string.
     * @param str The input string.
     * @return The numeric part of the string.
     *         Returns -1 if the string does not contain a numeric part.
     */
    key_t ExtractNumeric(const std::string& str) {
        std::string numberString;

        // Find the number of leading digits in the input string
        size_t numDigits = 0;
        std::string start_digit = "";
        while (numDigits < str.length() && std::isdigit(str[numDigits])) {
            numberString += str[numDigits];
            ++numDigits;          
        }

        if (numDigits == 0)
        {
            return -1;
        }

        if (numDigits == 1)
        {
            // this case is to avoid shared memory when there is just 0 or any negative value in front of edge.
            if (std::stoi(numberString) <= 0)
            {
                return -1;
            }
        }

        return std::stoi(numberString);
    }

#ifdef __linux__
    /**
     * @brief Creates a shared memory segment with the given key.
     * @param key The key for the shared memory segment.
     */
    void createSharedMemory(key_t key)
    {
        shmId_create = shmget(key, 256, IPC_CREAT | 0666);

        if (shmId_create == -1) {
            std::cerr << "Failed to create shared memory segment." << std::endl;
        }

        // Attach the shared memory segment to the process's address space
        sharedData_create = static_cast<char*>(shmat(shmId_create, NULL, 0));
        if (sharedData_create == reinterpret_cast<char*>(-1)) {
            std::cerr << "Failed to attach shared memory segment." << std::endl;
            sharedData_create = nullptr;
        }
    }

    /**
     * @brief Retrieves an existing shared memory segment with the given key.
     *        Waits until the shared memory segment is created by the writer process.
     * @param key The key for the shared memory segment.
     */
    void getSharedMemory(key_t key)
    {
        int retry = 0;
        const int MAX_RETRY = 100;
        while (retry < MAX_RETRY) {
            // Get the shared memory segment created by Writer
            shmId_get = shmget(key, 256, 0666);
            // Check if shared memory exists
            if (shmId_get != -1) {
                break; // Break the loop if shared memory exists
            }

            std::cout << "Shared memory does not exist. Make sure the writer process is running." << std::endl;
            sleep(1); // Sleep for 1 second before checking again
            retry++;
        }

        if (shmId_get == -1) {
            std::cerr << "Failed to get shared memory segment after max retries." << std::endl;
            return;
        }

        // Attach the shared memory segment to the process's address space
        sharedData_get = static_cast<char*>(shmat(shmId_get, NULL, 0));
        if (sharedData_get == reinterpret_cast<char*>(-1)) {
            std::cerr << "Failed to attach shared memory segment." << std::endl;
            sharedData_get = nullptr;
        }
    }
#endif

    /**
     * @brief Parses a file containing port and number mappings and returns a map of the values.
     * @param filename The name of the file to parse.
     * @return A map of port names and their corresponding numbers.
     */
    map<string,int> mapParser(string filename){
        map<string,int> ans;
        auto str_map = concore_base::safe_literal_eval_dict(filename, {});
        for (const auto& kv : str_map) {
            try {
                ans[kv.first] = std::stoi(kv.second);
            } catch (...) {
                ans[kv.first] = 0;
            }
        }
        return ans;
    }

    /**
     * @brief function to compare and determine whether file content has been changed.
     * @return true if the content has not changed, false otherwise.
     */
    bool unchanged(){
        if(olds.compare(s)==0){
            s = "";
            return true;
        }
        else{
            olds = s;
            return false;
        }
    }

    /**
     * @brief Parses a string and extracts a vector of double values.
     * @param f The input string to parse.
     * @return A vector of double values extracted from the input string.
     */
    vector<double> parser(string f){
        return concore_base::parselist_double(f);
    }

    /**
     * @brief deviate the read to either the SM (Shared Memory) or FM (File Method) communication protocol based on iport and oport.
     * @param port The port number.
     * @param name The name of the file.
     * @param initstr The initial string
     * @return 
     */
    vector<double> read(int port, string name, string initstr)
    {
        if(communication_iport == 1)
        {
            return read_SM(port, name, initstr);
        }

        return read_FM(port, name, initstr);
    }

    /**
     * @brief Reads data from a specified port and name using the FM (File Method) communication protocol.
     * @param port The port number.
     * @param name The name of the file.
     * @param initstr The initial string.
     * @return a string of file content
     */
    vector<double> read_FM(int port, string name, string initstr){
        chrono::milliseconds timespan((int)(1000*delay));
        this_thread::sleep_for(timespan);
        string ins;
        try {
            ifstream infile;
            infile.open(inpath+to_string(port)+"/"+name, ios::in);
            if(infile) {
                ostringstream ss;
                ss << infile.rdbuf(); // reading data
                ins = ss.str(); //saving data as string
                infile.close();
            }
            else {
                throw 505;}
        }
        catch (...) {
            ins = initstr;
        }
        
        int retry = 0;
        const int MAX_RETRY = 100;
        while ((int)ins.length()==0 && retry < MAX_RETRY){
            this_thread::sleep_for(timespan);
            try{
                ifstream infile;
                infile.open(inpath+to_string(port)+"/"+name, ios::in);
                if(infile) {
                    ostringstream ss;
                    ss << infile.rdbuf(); // reading data
                    ins = ss.str();
                    retrycount++;
                    infile.close();
                }
                else{
                    retrycount++;
                    throw 505;
                }
            }
            //observed retry count in C++ from various tests is approx 80.
            catch(...){
                cout<<"Read error";
            }
            retry++;
        }
        s += ins;

        vector<double> inval = parser(ins);
        if(inval.empty())
            inval = parser(initstr);
        if(inval.empty())
            return inval;
        simtime = simtime > inval[0] ? simtime : inval[0];

        //returning a string with data excluding simtime
        inval.erase(inval.begin());
        return inval;

    }

    /**
     * @brief Reads data from the shared memory segment based on the specified port and name.
     * @param port The port number.
     * @param name The name of the file.
     * @param initstr The initial string to use if the shared memory is not found.
     * @return string of file content
     */
    vector<double> read_SM(int port, string name, string initstr){
        chrono::milliseconds timespan((int)(1000*delay));
        this_thread::sleep_for(timespan);
        string ins = "";
        try {
        if (shmId_get != -1) {
            if (sharedData_get && sharedData_get[0] != '\0') {
                std::string message(sharedData_get, strnlen(sharedData_get, 256));
                ins = message;
            } 
            else 
            {
                throw 505;
            }
        } 
        else 
        {
            throw 505;
        }
        } catch (...) {
            ins = initstr;
        }
        
        int retry = 0;
        const int MAX_RETRY = 100;
        while ((int)ins.length()==0 && retry < MAX_RETRY){
            this_thread::sleep_for(timespan);
            try{
                if(shmId_get != -1) {
                    std::string message(sharedData_get, strnlen(sharedData_get, 256));
                    ins = message;
                    retrycount++;
                }
                else{
                    retrycount++;
                    throw 505;
                }
            }
            //observed retry count in C++ from various tests is approx 80.
            catch(...){
                std::cout << "Read error" << std::endl;
            }
            retry++;
        }
        s += ins;

        vector<double> inval = parser(ins);
        if(inval.empty())
            inval = parser(initstr);
        if(inval.empty())
            return inval;
        simtime = simtime > inval[0] ? simtime : inval[0];

        //returning a string with data excluding simtime
        inval.erase(inval.begin());
        return inval;

    }

    /**
     * @brief deviate the write to either the SM (Shared Memory) or FM (File Method) communication protocol based on iport and oport.
     * @param port The port number.
     * @param name The name of the file.
     * @param val The vector of double values to write.
     * @param delta The delta value (default: 0).
     */
    void write(int port, string name, vector<double> val, int delta=0)
    {
        if(communication_oport == 1)
        {
            return write_SM(port, name, val, delta);
        }

        return write_FM(port, name, val, delta);
    }


    /**
     * @brief deviate the write to either the SM (Shared Memory) or FM (File Method) communication protocol based on iport and oport.
     * @param port The port number.
     * @param name The name of the file.
     * @param val The string to write.
     * @param delta The delta value (default: 0).
     */    
    void write(int port, string name, string val, int delta=0)
    {
        if(communication_oport == 1)
        {
            return write_SM(port, name, val, delta);
        }

        return write_FM(port, name, val, delta);
    }

    /**
     * @brief write method, accepts a vector double and writes it to the file
     * @param port The port number.
     * @param name The name of the file.
     * @param val The string to write.
     * @param delta The delta value (default: 0).
     */
    void write_FM(int port, string name, vector<double> val, int delta=0){

        try {
            ofstream outfile;
            outfile.open(outpath+to_string(port)+"/"+name, ios::out);
            if(outfile){
                val.insert(val.begin(),simtime+delta);
                outfile<<'[';
                for(int i=0;i<val.size()-1;i++)
                    outfile<<val[i]<<',';
                outfile<<val[val.size()-1]<<']';
                outfile.close();
                // simtime must not be mutated here (issue #385).
                }
            else{
                throw 505;
                }
            }

        catch(...){
            cout<<"skipping +"<<outpath<<port<<" /"<<name;
        }
    }

    /**
     * @brief write method, accepts a string and writes it to the file
     * @param port The port number.
     * @param name The name of the file.
     * @param val The string to write.
     * @param delta The delta value (default: 0).
     */
    void write_FM(int port, string name, string val, int delta=0){
        chrono::milliseconds timespan((int)(2000*delay));
        this_thread::sleep_for(timespan);
        try {
            string temp;
            ofstream outfile;
            outfile.open(outpath+to_string(port)+"/"+name, ios::out);
            if(outfile){
                outfile<<val;
                outfile.close();
            }
            else throw 505;
        }
        catch(...){
            cout<<"skipping +"<<outpath<<port<<" /"<<name;
        }
    }

    /**
     * @brief Writes a vector of double values to the shared memory segment based on the specified port and name.
     * @param port The port number.
     * @param name The name of the file.
     * @param val The vector of double values to write.
     * @param delta The delta value (default: 0).
     */
    void write_SM(int port, string name, vector<double> val, int delta=0){

        try {
            std::ostringstream outfile;
            if(shmId_create != -1){
                val.insert(val.begin(),simtime+delta);
                outfile<<'[';
                for(int i=0;i<val.size()-1;i++)
                    outfile<<val[i]<<',';
                outfile<<val[val.size()-1]<<']';
                std::string result = outfile.str();
                std::strncpy(sharedData_create, result.c_str(), 256 - 1);
                // simtime must not be mutated here (issue #385).
                }
            else{
                throw 505;
                }
            }

        catch(...){
            cout<<"skipping +"<<outpath<<port<<" /"<<name;
        }
    }

    /**
     * @brief Writes a string to the shared memory segment based on the specified port and name.
     * @param port The port number.
     * @param name The name of the file.
     * @param val The string to write.
     * @param delta The delta value (default: 0).
     */
    void write_SM(int port, string name, string val, int delta=0){
        chrono::milliseconds timespan((int)(2000*delay));
        this_thread::sleep_for(timespan);
        try {
            if(shmId_create != -1){
                std::strncpy(sharedData_create, val.c_str(), 256 - 1);
            }
            else throw 505;
        }
        catch(...){
            cout<<"skipping +"<<outpath<<port<<" /"<<name;
        }
    }
    
#ifdef CONCORE_USE_ZMQ
    /**
     * @brief Registers a ZMQ port for use with read()/write().
     * @param port_name The ZMQ port name.
     * @param port_type "bind" or "connect".
     * @param address The ZMQ address.
     * @param socket_type_str The socket type string.
     */
    void init_zmq_port(string port_name, string port_type, string address, string socket_type_str) {
        if (zmq_ports.count(port_name)) return;
        int sock_type = concore_base::zmq_socket_type_from_string(socket_type_str);
        if (sock_type == -1) {
            cerr << "init_zmq_port: unknown socket type '" << socket_type_str << "'" << endl;
            return;
        }
        zmq_ports[port_name] = new concore_base::ZeroMQPort(port_type, address, sock_type);
    }

    /**
     * @brief Reads data from a ZMQ port. Strips simtime prefix, updates simtime.
     * @param port_name The ZMQ port name.
     * @param name The name of the file.
     * @param initstr The initial string.
     * @return a vector of double values
     */
    vector<double> read_ZMQ(string port_name, string name, string initstr) {
        auto it = zmq_ports.find(port_name);
        if (it == zmq_ports.end()) {
            cerr << "read_ZMQ: port '" << port_name << "' not initialized" << endl;
            return parser(initstr);
        }
        vector<double> inval = it->second->recv_with_retry();
        if (inval.empty())
            inval = parser(initstr);
        if (inval.empty()) return inval;
        simtime = simtime > inval[0] ? simtime : inval[0];
        s += port_name;
        inval.erase(inval.begin());
        return inval;
    }

    /**
     * @brief Writes a vector of double values to a ZMQ port. Prepends simtime+delta.
     * @param port_name The ZMQ port name.
     * @param name The name of the file.
     * @param val The vector of double values to write.
     * @param delta The delta value (default: 0).
     */
    void write_ZMQ(string port_name, string name, vector<double> val, int delta=0) {
        auto it = zmq_ports.find(port_name);
        if (it == zmq_ports.end()) {
            cerr << "write_ZMQ: port '" << port_name << "' not initialized" << endl;
            return;
        }
        val.insert(val.begin(), simtime + delta);
        it->second->send_with_retry(val);
        // simtime must not be mutated here (issue #385).
    }

    /**
     * @brief Writes a string to a ZMQ port.
     * @param port_name The ZMQ port name.
     * @param name The name of the file.
     * @param val The string to write.
     * @param delta The delta value (default: 0).
     */
    void write_ZMQ(string port_name, string name, string val, int delta=0) {
        auto it = zmq_ports.find(port_name);
        if (it == zmq_ports.end()) {
            cerr << "write_ZMQ: port '" << port_name << "' not initialized" << endl;
            return;
        }
        chrono::milliseconds timespan((int)(2000*delay));
        this_thread::sleep_for(timespan);
        it->second->send_string_with_retry(val);
    }

    /**
     * @brief deviate the read to ZMQ communication protocol when port identifier is a string key.
     * @param port_name The ZMQ port name.
     * @param name The name of the file.
     * @param initstr The initial string.
     * @return 
     */
    vector<double> read(string port_name, string name, string initstr) {
        return read_ZMQ(port_name, name, initstr);
    }

    /**
     * @brief deviate the write to ZMQ communication protocol when port identifier is a string key.
     * @param port_name The ZMQ port name.
     * @param name The name of the file.
     * @param val The vector of double values to write.
     * @param delta The delta value (default: 0).
     */
    void write(string port_name, string name, vector<double> val, int delta=0) {
        return write_ZMQ(port_name, name, val, delta);
    }

    /**
     * @brief deviate the write to ZMQ communication protocol when port identifier is a string key.
     * @param port_name The ZMQ port name.
     * @param name The name of the file.
     * @param val The string to write.
     * @param delta The delta value (default: 0).
     */
    void write(string port_name, string name, string val, int delta=0) {
        return write_ZMQ(port_name, name, val, delta);
    }
#endif // CONCORE_USE_ZMQ

    /**
     * @brief Strips leading and trailing whitespace from a string.
     * @param str The input string.
     * @return The stripped string.
     */
    string stripstr(string str){
        return concore_base::stripstr(str);
    }

    /**
     * @brief Strips surrounding single or double quotes from a string.
     * @param str The input string.
     * @return The unquoted string.
     */
    string stripquotes(string str){
        return concore_base::stripquotes(str);
    }

    /**
     * @brief Parses a dict-formatted string into a string-to-string map.
     * @param str The input string in {key: val, ...} format.
     * @return A map of key-value string pairs.
     */
    map<string, string> parsedict(string str){
        return concore_base::parsedict(str);
    }

    /**
     * @brief Sets maxtime from the concore.maxtime file, falling back to defaultValue.
     * @param defaultValue The fallback value if the file is missing.
     */
    void default_maxtime(int defaultValue){
        maxtime = (int)concore_base::load_maxtime(
            inpath + "/1/concore.maxtime", (double)defaultValue);
    }

    /**
     * @brief Loads simulation parameters from concore.params into the params map.
     */
    void load_params(){
        params = concore_base::load_params(inpath + "/1/concore.params");
    }

    /**
     * @brief Returns the value of a param by name, or a default if not found.
     * @param n The parameter name.
     * @param i The default value.
     * @return The parameter value or the default.
     */
    string tryparam(string n, string i){
        return concore_base::tryparam(params, n, i);
    }

    /**
     * @brief Initializes the system with the given input values.
     * @param f The input string containing the values.
     * @return A vector of double values representing the initialized system state.
     */
    vector<double> initval(string f){
        //parsing
        vector<double> val = parser(f);

        if (val.empty()) return val;

        //determining simtime
        simtime = val[0];

        //returning the rest of the values(except simtime) in val
        val.erase(val.begin());
        return val;
    }    
};

#endif // CONCORE_HPP
