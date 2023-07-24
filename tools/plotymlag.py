import concore
import numpy as np
import matplotlib.pyplot as plt
import time

size = 10
lag = concore.tryparam("lag", 0) 
print("plot ym with lag="+str(lag))

concore.delay = 0.005
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
ut = []
ymt = []
ym = []
for i in range(0,size):
   ym.append(concore.initval(init_simtime_ym))
cur = 0
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym[cur] = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym[cur])
    print(" ym="+str(ym[cur]))
    ymt.append(np.array(ym[(cur-lag) % size]).T)
    cur = (cur+1) % size
print("retry="+str(concore.retrycount))

#################

# plot inputs and outputs
ym1 = [x[0].item() for x in ymt]
ym2 = [x[1].item() for x in ymt]
Nsim = len(ym1)

plt.figure()
plt.subplot(211)
plt.plot(range(Nsim), ym1)
plt.ylabel('MAP (mmHg)')
plt.legend(['MAP'], loc=0)
plt.subplot(212)
plt.plot(range(Nsim), ym2)
plt.xlabel('Cycles '+str(concore.params))
plt.ylabel('HR (bpm)')
plt.legend(['HR'], loc=0)
plt.savefig("hrmap.pdf")
plt.show()
