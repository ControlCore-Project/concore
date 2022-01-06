import concore
import os
import time

concore.delay = 0.01
Nsim = 100
init_simtime_u = "[0.0,0.0,0.0]"
init_simtime_ym = "[0.0,0.0,0.0]"

u = concore.initval(init_simtime_u)
while(concore.simtime<Nsim):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    u[0] = ym[0]+1
    if concore.simtime==10:
        u = concore.initval(init_simtime_u)       
        concore.simtime = -2
        print(os.listdir(concore.inpath+"1/"))
        time.sleep(3)
        os.remove(concore.inpath+"1/ym")
    print("ym="+str(ym[0])+" u="+str(u[0])+" time="+str(concore.simtime));
    concore.write(1,"u",u);
concore.write(1,"u",init_simtime_u)
print("retry="+str(concore.retrycount))
