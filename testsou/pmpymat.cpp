#include "concore.hpp"
//instead of below, this file will be C++ equivalent of pmpymat.py
#include <string>
#include <vector>
#include <iomanip> //setprecision

using namespace std;

int main()
{
  Concore concore;
  concore.delay = 0.01;
  int Nsim = 100;
  string init_simtime_u = "[0.0,0.0,0.0]";
  string init_simtime_ym = "[0.0,0.0,0.0]";

  vector<double> ym = concore.initval(init_simtime_ym);
  vector<double> u;
  while(concore.simtime<Nsim){
    while (concore.unchanged()){
      u = concore.read(1,"u",init_simtime_u);
    }

    ym[0]  = u[0]+10000;

    cout<<setprecision(1)<<fixed<<"ym="<<ym[0]<<" u="<<u[0]<<endl;
    concore.write(1,"ym",ym,1);
  }
  concore.write(1,"ym",init_simtime_ym);
  cout<<"retry="<<concore.retrycount<<endl;
}

