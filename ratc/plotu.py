import concore
import logging
import numpy as np
import matplotlib.pyplot as plt
import time
logging.info("plot u")

concore.delay = 0.005
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
ut = []
ymt = []

plt.ion()       #interactive plotting
plt.figure()    #initialize the figure before the loop

u = concore.initval(init_simtime_u)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    concore.write(1,"u",u)
    logging.debug(f"u={u}")
    ut.append(np.array(u).T)

    #update plot every 5 cycles to prevent drawing lag
    if len(ut) % 5 == 0: 
        plt.clf() # clear the figure to draw the fresh frame

        u1 = [x[0].item() for x in ut]
        u2 = [x[1].item() for x in ut]
        u3 = [x[2].item() for x in ut]
        u4 = [x[3].item() for x in ut]
        u5 = [x[4].item() for x in ut]
        u6 = [x[5].item() for x in ut]

        Nsim = len(u1)
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
        plt.tight_layout()
        
        plt.pause(0.001)

logging.info(f"retry={concore.retrycount}")

#post-simulation cleanup
plt.ioff()               
plt.savefig("stim.pdf")
plt.show()


