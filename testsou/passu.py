import concore
import numpy as np
print("pass u")

concore.delay = 0.005
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
u = concore.initval(init_simtime_u)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    concore.write(1,"u",u)
    print("u="+str(u))
print("retry="+str(concore.retrycount))

