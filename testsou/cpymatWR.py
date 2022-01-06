import concore
import os
import time

concore.delay = 0.01
Nsim = 10
init_simtime_u = "[0.0,0.0,0.0]"
init_simtime_u_reset = "[-2.0,0.0,0.0]"
init_simtime_ym = "[0.0,0.0,0.0]"

for i in range(0,20):
  u = concore.initval(init_simtime_u)
  while(concore.simtime<Nsim):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    u[0] = ym[0]+1
    print("ym="+str(ym[0])+" u="+str(u[0])+" time="+str(concore.simtime));
    concore.write(1,"u",u);
  concore.write(1,"u",init_simtime_u_reset)
  concore.s = ''
  ym = concore.read(1,"ym",init_simtime_ym)
  if concore.simtime>=Nsim:
      concore.s = ''
      ym = concore.read(1,"ym",init_simtime_ym)
  print("done "+str(i))
print("retry="+str(concore.retrycount))
