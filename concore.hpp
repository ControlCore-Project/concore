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
#include <sys/sem.h>
#include <sys/shm.h>
#include <unistd.h>
#include <cerrno>
union semun { //not defined by glibc; needed for semctl SETVAL
    int val;
    struct semid_ds* buf;
    unsigned short* array;
};
#endif
#include <cstring>
#include <cctype>
#include <cstdint>
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

    static constexpr size_t SHM_SIZE = 4096;
    //SHM layout: [0..7]=uint64 seq#, [8..]=payload.  odd=writing, even=ready.
    //A seqlock-style protocol: writer flips even->odd, memcpy, fence,
    //flips odd->even.  Reader loads seq, copies payload, re-loads seq,
    //accepts only if both loads match and seq is even.  See issue #195.
    static constexpr size_t SHM_HEADER_SIZE = 8;
    static constexpr size_t SHM_PAYLOAD_MAX = SHM_SIZE - SHM_HEADER_SIZE - 1;

    int shmId_create = -1;
    int shmId_get = -1;

    char* sharedData_create = nullptr;
    char* sharedData_get = nullptr;
    // File sharing:- 0, Shared Memory:- 1
    int communication_iport = 0;  // iport refers to input port
    int communication_oport = 0;  // oport refers to input port
#ifdef __linux__
    //POSIX semaphores keyed by (shm_key+1).  Idempotent across processes.
    int semId_create = -1;
    int semId_get = -1;
#endif

#ifdef CONCORE_USE_ZMQ
    map<string, concore_base::ZeroMQPort*> zmq_ports;
#endif

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
        vector<double> data;
    };

    double delay = 1;
    int retrycount = 0;
    double simtime;
    int maxtime = 100;
    map <string, int> iport;
    map <string, int> oport;
    map <string, string> params;
    ReadStatus last_read_status = ReadStatus::SUCCESS;

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
        if (semId_create != -1) {
            semctl(semId_create, 0, IPC_RMID);
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
#ifdef __linux__
          , semId_create(other.semId_create), semId_get(other.semId_get)
#endif
    {
        other.shmId_create = -1;
        other.shmId_get = -1;
        other.sharedData_create = nullptr;
        other.sharedData_get = nullptr;
        other.communication_iport = 0;
        other.communication_oport = 0;
#ifdef __linux__
        other.semId_create = -1;
        other.semId_get = -1;
#endif
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
        if (semId_create != -1)
            semctl(semId_create, 0, IPC_RMID);
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
#ifdef __linux__
        semId_create = other.semId_create;
        semId_get = other.semId_get;
#endif

        other.shmId_create = -1;
        other.shmId_get = -1;
        other.sharedData_create = nullptr;
        other.sharedData_get = nullptr;
        other.communication_iport = 0;
        other.communication_oport = 0;
#ifdef __linux__
        other.semId_create = -1;
        other.semId_get = -1;
#endif

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
    static inline uint64_t shm_load_seq(const char* base) {
        uint64_t v;
        __atomic_load(reinterpret_cast<const uint64_t*>(base), &v, __ATOMIC_ACQUIRE);
        return v;
    }

    static inline void shm_store_seq(char* base, uint64_t v) {
        __atomic_store(reinterpret_cast<uint64_t*>(base), &v, __ATOMIC_RELEASE);
    }

    // Seqlock-style snapshot read: returns the payload on success, or
    // std::string() (empty) if the seq# is missing, odd (write in progress),
    // or changed between the two reads. The caller can retry without
    // taking the semaphore.
    static std::string shm_read_payload(const char* base) {
        if (base == nullptr) return std::string();
        uint64_t s1 = shm_load_seq(base);
        if (s1 == 0 || (s1 & 1u)) return std::string();
        std::string out(base + SHM_HEADER_SIZE,
                        strnlen(base + SHM_HEADER_SIZE, SHM_PAYLOAD_MAX));
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        uint64_t s2 = shm_load_seq(base);
        if (s1 != s2) return std::string();
        return out;
    }

    static int shm_sem_create(key_t key) {
        // Try to create as the original owner. If it already exists,
        // attach without resetting its value (a stale semaphore would
        // reset valid in-use state otherwise).
        int id = semget(key, 1, IPC_CREAT | IPC_EXCL | 0666);
        if (id >= 0) {
            semun arg{};
            arg.val = 1;
            if (semctl(id, 0, SETVAL, arg) < 0) return -1;
            return id;
        }
        // EEXIST means another process got here first; just open it.
        id = semget(key, 1, 0666);
        return id < 0 ? -1 : id;
    }

    static void shm_sem_acquire(int id) {
        if (id < 0) return;
        sembuf sb{};
        sb.sem_num = 0;
        sb.sem_op = -1;
        sb.sem_flg = 0;
        while (semop(id, &sb, 1) == -1) {
            if (errno != EINTR) {
                std::cerr << "semop(acquire) failed errno=" << errno << std::endl;
                return;
            }
        }
    }

    static void shm_sem_release(int id) {
        if (id < 0) return;
        sembuf sb{};
        sb.sem_num = 0;
        sb.sem_op = 1;
        sb.sem_flg = 0;
        while (semop(id, &sb, 1) == -1) {
            if (errno != EINTR) {
                std::cerr << "semop(release) failed errno=" << errno << std::endl;
                return;
            }
        }
    }
#endif

#ifdef __linux__
    /**
     * @brief Creates a shared memory segment with the given key.
     * @param key The key for the shared memory segment.
     */
    void createSharedMemory(key_t key)
    {
        shmId_create = shmget(key, SHM_SIZE, IPC_CREAT | 0666);

        if (shmId_create == -1) {
            std::cerr << "Failed to create shared memory segment." << std::endl;
            return;
        }

        // Verify the segment is large enough (shmget won't resize an existing segment)
        struct shmid_ds shm_info;
        if (shmctl(shmId_create, IPC_STAT, &shm_info) == 0 && shm_info.shm_segsz < SHM_SIZE) {
            std::cerr << "Shared memory segment too small (" << shm_info.shm_segsz
                      << " bytes, need " << SHM_SIZE << "). Removing and recreating." << std::endl;
            shmctl(shmId_create, IPC_RMID, nullptr);
            shmId_create = shmget(key, SHM_SIZE, IPC_CREAT | 0666);
            if (shmId_create == -1) {
                std::cerr << "Failed to recreate shared memory segment." << std::endl;
                return;
            }
        }

        // Attach the shared memory segment to the process's address space
        sharedData_create = static_cast<char*>(shmat(shmId_create, NULL, 0));
        if (sharedData_create == reinterpret_cast<char*>(-1)) {
            std::cerr << "Failed to attach shared memory segment." << std::endl;
            sharedData_create = nullptr;
            return;
        }

        semId_create = shm_sem_create(key + 1);
        if (semId_create < 0) {
            std::cerr << "Failed to create shared memory semaphore." << std::endl;
        }

        //initialise header
        shm_store_seq(sharedData_create, uint64_t{0});
        sharedData_create[SHM_HEADER_SIZE] = '\0';
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
            shmId_get = shmget(key, SHM_SIZE, 0666);
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
            return;
        }

        //attach reader-side semaphore (writer owns its lifetime)
        semId_get = semget(key + 1, 1, 0666);
        if (semId_get < 0) {
            //no semaphore: reads fall back to seq# alone
            semId_get = -1;
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
     * @brief Parses a literal string into a ConcoreValue representation.
     * @param f The input string to parse.
     * @return A ConcoreValue obtained by parsing the input string.
     */
    concore_base::ConcoreValue parse_literal(string f){
        return concore_base::parse_literal(f);
    }

    /**
     * @brief Flattens a ConcoreValue into a vector of numeric (double) values.
     * @param v The ConcoreValue to flatten.
     * @return A vector of double values obtained by flattening the input.
     */
    vector<double> flatten_numeric(const concore_base::ConcoreValue& v){
        return concore_base::flatten_numeric(v);
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

    ReadResult read_result(int port, string name, string initstr)
    {
        ReadResult result;
        result.data = read(port, name, initstr);
        result.status = last_read_status;
        return result;
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
        ReadStatus status = ReadStatus::SUCCESS;
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
                status = ReadStatus::FILE_NOT_FOUND;
                throw 505;}
        }
        catch (...) {
            ins = initstr;
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::FILE_NOT_FOUND;
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
        if ((int)ins.length()==0)
            status = ReadStatus::RETRIES_EXCEEDED;
        s += ins;

        vector<double> inval = parser(ins);
        if(inval.empty()) {
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::PARSE_ERROR;
            inval = parser(initstr);
        }
        if(inval.empty()) {
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::PARSE_ERROR;
            last_read_status = status;
            return inval;
        }
        simtime = simtime > inval[0] ? simtime : inval[0];
        last_read_status = status;

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
        ReadStatus status = ReadStatus::SUCCESS;
#ifdef __linux__
        if (shmId_get == -1 || sharedData_get == nullptr) {
            status = ReadStatus::FILE_NOT_FOUND;
            ins = initstr;
        } else {
            std::string snap = shm_read_payload(sharedData_get);
            if (snap.empty()) {
                ins = initstr;
                if (status == ReadStatus::SUCCESS)
                    status = ReadStatus::FILE_NOT_FOUND;
            } else {
                ins = snap;
            }
        }
#else
        ins = initstr;
        status = ReadStatus::FILE_NOT_FOUND;
#endif

        int retry = 0;
        const int MAX_RETRY = 100;
#ifdef __linux__
        while ((int)ins.length()==0 && retry < MAX_RETRY){
            this_thread::sleep_for(timespan);
            if(shmId_get != -1 && sharedData_get != nullptr) {
                std::string snap = shm_read_payload(sharedData_get);
                if (!snap.empty()) {
                    ins = snap;
                    retrycount++;
                }
            }
            else{
                retrycount++;
            }
            retry++;
        }
#else
        while ((int)ins.length()==0 && retry < MAX_RETRY){
            this_thread::sleep_for(timespan);
            retry++;
        }
#endif
        if ((int)ins.length()==0)
            status = ReadStatus::RETRIES_EXCEEDED;
        s += ins;

        vector<double> inval = parser(ins);
        if(inval.empty()) {
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::PARSE_ERROR;
            inval = parser(initstr);
        }
        if(inval.empty()) {
            if (status == ReadStatus::SUCCESS)
                status = ReadStatus::PARSE_ERROR;
            last_read_status = status;
            return inval;
        }
        simtime = simtime > inval[0] ? simtime : inval[0];
        last_read_status = status;

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

        catch (const std::exception &e) {
            // Surface the error message and rethrow so callers (or the runtime)
            // see the failure instead of silently proceeding with truncated data.
            std::cerr << e.what() << std::endl;
            throw;
        } catch (...) {
            // Unknown exception: rethrow to avoid silent suppression.
            throw;
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
        catch (const std::exception &e) {
            std::cerr << e.what() << std::endl;
            throw;
        } catch (...) {
            throw;
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

        std::ostringstream outfile;
        val.insert(val.begin(),simtime+delta);
        outfile<<'[';
        for(int i=0;i<val.size()-1;i++)
            outfile<<val[i]<<',';
        outfile<<val[val.size()-1]<<']';
        std::string result = outfile.str();
        if (result.size() >= SHM_SIZE) {
            throw std::runtime_error(
                "concore SHM write failed: payload (" +
                std::to_string(result.size()) +
                " bytes) exceeds SHM_SIZE (" +
                std::to_string(SHM_SIZE) +
                "). Aborting. No data written. Increase SHM_SIZE in concore.hpp."
            );
        }
        const size_t max_payload = SHM_PAYLOAD_MAX;
        if (result.size() > max_payload) {
            std::cerr << "ERROR: write_SM payload (" << result.size()
                      << " bytes) exceeds " << max_payload
                      << "-byte shared memory limit. Data truncated!" << std::endl;
            result.resize(max_payload);
        }
        try {
            if(shmId_create == -1){
                throw 505;
            }
            if (sharedData_create == nullptr)
                throw 506;
#ifdef __linux__
            shm_sem_acquire(semId_create);
#endif
            {
                auto* seqp = reinterpret_cast<uint64_t*>(sharedData_create);
                // Mark "writing" by flipping seq to odd.
                (void)__atomic_fetch_add(seqp, uint64_t{1}, __ATOMIC_ACQ_REL);
                std::memcpy(sharedData_create + SHM_HEADER_SIZE,
                            result.c_str(), result.size());
                sharedData_create[SHM_HEADER_SIZE + result.size()] = '\0';
                __atomic_thread_fence(__ATOMIC_RELEASE);
                // Publish by flipping seq to even.
                (void)__atomic_fetch_add(seqp, uint64_t{1}, __ATOMIC_ACQ_REL);
            }
#ifdef __linux__
            shm_sem_release(semId_create);
#endif
            // simtime must not be mutated here (issue #385).
        }

        catch (const std::exception &e) {
            std::cerr << e.what() << std::endl;
            throw;
        } catch (...) {
            throw;
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
        if (val.size() >= SHM_SIZE) {
            throw std::runtime_error(
                "concore SHM write failed: payload (" +
                std::to_string(val.size()) +
                " bytes) exceeds SHM_SIZE (" +
                std::to_string(SHM_SIZE) +
                "). Aborting. No data written. Increase SHM_SIZE in concore.hpp."
            );
        }
        try {
            if(shmId_create == -1){
                throw 505;
            }
            if (sharedData_create == nullptr)
                throw 506;
            const size_t max_payload = SHM_PAYLOAD_MAX;
            if (val.size() > max_payload) {
                std::cerr << "ERROR: write_SM payload (" << val.size()
                          << " bytes) exceeds " << max_payload
                          << "-byte shared memory limit. Data truncated!" << std::endl;
                val.resize(max_payload);
            }
#ifdef __linux__
            shm_sem_acquire(semId_create);
#endif
            {
                auto* seqp = reinterpret_cast<uint64_t*>(sharedData_create);
                (void)__atomic_fetch_add(seqp, uint64_t{1}, __ATOMIC_ACQ_REL);
                std::memcpy(sharedData_create + SHM_HEADER_SIZE,
                            val.c_str(), val.size());
                sharedData_create[SHM_HEADER_SIZE + val.size()] = '\0';
                __atomic_thread_fence(__ATOMIC_RELEASE);
                (void)__atomic_fetch_add(seqp, uint64_t{1}, __ATOMIC_ACQ_REL);
            }
#ifdef __linux__
            shm_sem_release(semId_create);
#endif
        }
        catch (const std::exception &e) {
            std::cerr << e.what() << std::endl;
            throw;
        } catch (...) {
            throw;
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
        ReadStatus status = ReadStatus::SUCCESS;
        auto it = zmq_ports.find(port_name);
        if (it == zmq_ports.end()) {
            cerr << "read_ZMQ: port '" << port_name << "' not initialized" << endl;
            status = ReadStatus::FILE_NOT_FOUND;
            last_read_status = status;
            return parser(initstr);
        }
        vector<double> inval = it->second->recv_with_retry();
        if (inval.empty()) {
            status = ReadStatus::TIMEOUT;
            inval = parser(initstr);
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

    ReadResult read_result(string port_name, string name, string initstr) {
        ReadResult result;
        result.data = read(port_name, name, initstr);
        result.status = last_read_status;
        return result;
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
