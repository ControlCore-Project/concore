import concore
import numpy as np

def pm(u):
  return u + 0.01

concore.default_maxtime(150) 
concore.delay = 0.02

init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

ym = np.array([concore.initval(init_simtime_ym)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    u = np.array([u]).T
    #####
    ym = pm(u)
    #####
    print(str(concore.simtime) + ". u="+str(u) + "ym="+str(ym));
    concore.write(1,"ym",list(ym.T[0]),delta=1)

print("retry="+str(concore.retrycount))

