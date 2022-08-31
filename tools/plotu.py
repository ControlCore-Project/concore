import concore
import numpy as np
import matplotlib.pyplot as plt
import time
print("plot u")

concore.delay = 0.005
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
ut = []
ymt = []
u = concore.initval(init_simtime_u)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    concore.write(1,"u",u)
    print("u="+str(u))
    ut.append(np.array(u).T)
print("retry="+str(concore.retrycount))

#################

# plot inputs and outputs
u1 = [x[0].item() for x in ut]
u2 = [x[1].item() for x in ut]
u3 = [x[2].item() for x in ut]
u4 = [x[3].item() for x in ut]
u5 = [x[4].item() for x in ut]
u6 = [x[5].item() for x in ut]

Nsim = len(u1)
plt.figure()
plt.subplot(321)
plt.plot(range(Nsim), u1)
plt.ylabel('Pw1 (s)')
plt.subplot(322)
plt.plot(range(Nsim), u2)
plt.ylabel('Pf1 (Hz)')
plt.subplot(323)
plt.plot(range(Nsim), u3)
plt.xlabel('Cycles')
plt.ylabel('Pw2 (s)')
plt.subplot(324)
plt.plot(range(Nsim), u4)
plt.ylabel('Pf2 (Hz)')
plt.subplot(325)
plt.plot(range(Nsim), u5)
plt.ylabel('Pw3 (s)')
plt.subplot(326)
plt.plot(range(Nsim), u6)
plt.xlabel('Cycles')
plt.ylabel('Pf3 (Hz)')
plt.savefig("stim.pdf")
plt.tight_layout()
plt.show()


