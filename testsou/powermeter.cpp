#include "concore.hpp"
#include <string>
#include <vector>
#include <chrono>
#include <iomanip> //setprecision

using namespace std;
int main(){

    cout<<"powermeter"<<endl;
    Concore concore;
    concore.delay = 0.07;
    int Nsim = 100;
    string init_simtime_u = "[0.0,0.0,0.0]";
    string init_simtime_ym = "[0.0,0.0,0.0]";
    int energy = 0;

    vector<double> ym = concore.initval(init_simtime_ym);
    vector<double> u;
    while(concore.simtime<Nsim){
        while (concore.unchanged()){
            u = concore.read(concore.iport["VC"],"u",init_simtime_u);
        }

        concore.write(concore.oport["VXP"],"u",u);

        while (concore.unchanged()){
            ym = concore.read(concore.iport["VP"],"ym",init_simtime_ym);
        }

        concore.write(concore.oport["VXC"],"ym",ym);

        cout<<"powermeter u=[";
        for(int j=0;j<u.size();j++){
            cout<<u[j];
            if(j!=u.size()-1)
                cout<<",";
        }
        cout<<"] ym=[";
        for(int j=0;j<ym.size();j++){
            cout<<ym[j];
            if(j!=ym.size()-1)
                cout<<",";
        }
        cout<<"]"<<endl;
    }

    cout<<"retry="<<concore.retrycount<<endl;

    return 0;
}