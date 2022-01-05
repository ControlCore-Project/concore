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

using namespace std;

class Concore{

    //private variables
    string s="",olds="";
    string inpath = "./in";
    string outpath = "./out";

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

    //accepts the file name as string and returns a string of file content
    vector<double> read(int port, string name, string initstr){
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

    //write method, accepts a vector double and writes it to the file
    void write(int port, string name, vector<double> val, int delta=0){

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
    void write(int port, string name, string val, int delta=0){
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
