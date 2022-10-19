import concore
import numpy as np
print("pass ym")

concore.delay = 0.005
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym)
    print(" ym="+str(ym))
print("retry="+str(concore.retrycount))

