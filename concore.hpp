// concore.hpp -- this C++ include file will be the equivalent of concore.py
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
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <cstring>
#include <cctype>

using namespace std;

class Concore{

private:
    //private variables
    string s="",olds="";
    string inpath = "./in";
    string outpath = "./out";

    int shmId_create;
    int shmId_get;

    char* sharedData_create;
    char* sharedData_get;
    // File sharing:- 0, Shared Memory:- 1
    int communication_iport = 0;
    int communication_oport = 0;

 public:
    double delay = 1;
    int retrycount = 0;
    double simtime;
    map <string, int> iport;
    map <string, int> oport;

    //Constructor to put in iport and oport values in map
    Concore(){
        iport = mapParser("concore.iport");
        oport = mapParser("concore.oport");   
        std::map<std::string, int>::iterator it_iport = iport.begin();
        std::map<std::string, int>::iterator it_oport = oport.begin();
        int iport_number = ExtractNumeric(it_iport->first);
        int oport_number = ExtractNumeric(it_oport->first);

        if(oport_number != -1)
        {
            communication_oport = 1;
            this->createSharedMemory(oport_number);
        }  

        if(iport_number != -1)
        {
            communication_iport = 1;
            this->getSharedMemory(iport_number);
        }    
    }

    ~Concore()
    {
        // Detach the shared memory segment from the process
        shmdt(sharedData_create);
        shmdt(sharedData_get);

        // Remove the shared memory segment
        shmctl(shmId_create, IPC_RMID, nullptr);
    }

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
            if (std::stoi(numberString) <= 0)
            {
                return -1;
            }
        }

        return std::stoi(numberString);
    }

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
        }
    }

    void getSharedMemory(key_t key)
    {
        while (true) {
            // Get the shared memory segment created by Writer
            shmId_get = shmget(key, 256, 0666);
            // Check if shared memory exists
            if (shmId_get != -1) {
                break; // Break the loop if shared memory exists
            }

            std::cout << "Shared memory does not exist. Make sure the writer process is running." << std::endl;
            sleep(1); // Sleep for 1 second before checking again
        }

        // Attach the shared memory segment to the process's address space
        sharedData_get = static_cast<char*>(shmat(shmId_get, NULL, 0));
    }

    map<string,int> mapParser(string filename){
        map<string,int> ans;

        ifstream portfile;
        string portstr;
        portfile.open(filename);
        if(portfile){
            ostringstream ss;
            ss << portfile.rdbuf();
            portstr = ss.str();
            portfile.close();
        }

        portstr[portstr.size()-1]=',';
        portstr+='}';
        int i=0;
        string portname="";
        string portnum="";

        while(portstr[i]!='}'){
            if(portstr[i]=='\''){
                i++;
                while(portstr[i]!='\''){
                    portname+=portstr[i];
                    i++;
                }
                ans.insert({portname,0});
            }

            if(portstr[i]==':'){
                i++;
                while(portstr[i]!=','){
                    portnum+=portstr[i];
                    i++;
                }
                ans[portname]=stoi(portnum);
                portnum="";
                portname="";
            }  
            i++;
        }
        return ans;
    }

    //function to compare and determine whether file content has been changed
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

    vector<double> parser(string f){
        vector<double> temp;
        string value = "";
    
        //Changing last bracket to comma to use comma as a delimiter
        f[f.length()-1]=',';

        for(int i=1;i<f.length();i++){
            if(f[i]!=',')
                value+=f[i];
            else{
                if((int)value.size()!=0)
                    temp.push_back(stod(value));
                
                //reset value
                value = "";
            }
        }
        return temp;
    }

    vector<double> read(int port, string name, string initstr)
    {
        if(communication_iport == 1)
        {
            return read_SM(port, name, initstr);
        }

        return read_FM(port, name, initstr);
    }

    //accepts the file name as string and returns a string of file content
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
        
        while ((int)ins.length()==0){
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
            
            
        }
        s += ins;

        vector<double> inval = parser(ins);
        simtime = simtime > inval[0] ? simtime : inval[0];

        //returning a string with data excluding simtime
        inval.erase(inval.begin());
        return inval;

    }

    //accepts the file name as string and returns a string of file content
    vector<double> read_SM(int port, string name, string initstr){
        chrono::milliseconds timespan((int)(1000*delay));
        this_thread::sleep_for(timespan);
        string ins = "";
        try {
        if (shmId_get != -1) {
            if (sharedData_get && sharedData_get[0] != '\0') {
                std::string message(sharedData_get, strnlen(sharedData_get, 256));
                ins = message;
                // std::cout << "Received message: " << message << " ins " << ins.length() << std::endl;
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
        
        while ((int)ins.length()==0){
            this_thread::sleep_for(timespan);
            try{
                if(shmId_get != -1) {
                    std::cout << "in read while\n";
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
                cout<<"Read error";
            }
        }
        s += ins;

        vector<double> inval = parser(ins);
        simtime = simtime > inval[0] ? simtime : inval[0];

        //returning a string with data excluding simtime
        inval.erase(inval.begin());
        return inval;

    }

    void write(int port, string name, vector<double> val, int delta=0)
    {
        if(communication_oport == 1)
        {
            return write_SM(port, name, val, delta);
        }

        return write_FM(port, name, val, delta);
    }

    void write(int port, string name, string val, int delta=0)
    {
        if(communication_oport == 1)
        {
            return write_SM(port, name, val, delta);
        }

        return write_FM(port, name, val, delta);
    }

    //write method, accepts a vector double and writes it to the file
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
                }
            else{
                throw 505;
                }
            }

        catch(...){
            cout<<"skipping +"<<outpath<<port<<" /"<<name;
        }
    }

    //write method, accepts a string and writes it to the file
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

    //write method, accepts a vector double and writes it to the file
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
                }
            else{
                throw 505;
                }
            }

        catch(...){
            cout<<"skipping +"<<outpath<<port<<" /"<<name;
        }
    }

    //write method, accepts a string and writes it to the file
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
    
    //Initialising
    vector<double> initval(string f){
        //parsing
        vector<double> val = parser(f);

        //determining simtime
        simtime = val[0];

        //returning the rest of the values(except simtime) in val
        val.erase(val.begin());
        return val;
    }    

};
