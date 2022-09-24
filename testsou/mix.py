import concore
import concore2
import numpy as np
import time

concore.delay = 0.005
concore2.delay = 0.005
concore2.inpath = concore.inpath
concore2.outpath = concore.outpath
concore2.simtime = 0
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
u1 = concore.initval(init_simtime_u)
u2 = concore.initval(init_simtime_u)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u1 = concore.read(concore.iport['U1'],"u",init_simtime_u)
    while concore2.unchanged():
        u2 = concore2.read(concore.iport['U2'],"u",init_simtime_u)
    print("u1="+str(u1)+" u2="+str(u2))
    concore.write(1,"u",list(np.array(u1)+np.array(u2)))
print("retry="+str(concore.retrycount))

