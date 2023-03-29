import concore
import numpy as np
import matplotlib.pyplot as plt
import time
print("plotym")

concore.delay = 0.02
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"
ymt = []
ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym)
    print("ym="+str(ym))
    ymt.append(np.array(ym).T)
print("retry="+str(concore.retrycount))

#################

# plot inputs and outputs
ym1 = [x[0].item() for x in ymt]

Nsim = len(ym1)
plt.figure()
plt.subplot(111)
plt.plot(range(Nsim), ym1)
plt.ylabel('ym')
plt.legend(['ym'], loc=0)
plt.xlabel('Cycles')
plt.savefig("ym.pdf")
plt.show()
