import concore
import numpy as np
import matplotlib.pyplot as plt
import time
print("plotym")

concore.delay = 0.02
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0, 103, 0]"
ymt = []

ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym)
    print("ym="+str(ym))
    ymt.append(ym)
print("retry="+str(concore.retrycount))

#################
ylabelstring = ['Heart rate (bpm)', 'MAP (mmHg)']
# plot inputs and outputs

for k in range(2):
    vv = []
    for x in ymt:
        vv.append(x[k])

    Nsim = len(vv)
    plt.figure(k)
    plt.plot(range(Nsim), vv)
    plt.ylabel(ylabelstring[k])
   
    plt.xlabel('Heart cycles')
    plt.savefig("ym" + str(k) +".pdf")
plt.show()
