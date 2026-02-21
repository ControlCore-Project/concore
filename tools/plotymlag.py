import concore
import logging
import numpy as np
import matplotlib.pyplot as plt
import time

size = 10
lag = concore.tryparam("lag", 0) 
logging.info(f"plot ym with lag={lag}")

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

plt.ion() # enable interactive mode
fig, (ax1, ax2) = plt.subplots(2, 1)

line1, = ax1.plot([], [])
ax1.set_ylabel('MAP (mmHg)')
ax1.legend(['MAP'], loc=0)

line2, = ax2.plot([], [])
ax2.set_xlabel('Cycles '+str(concore.params))
ax2.set_ylabel('HR (bpm)')
ax2.legend(['HR'], loc=0)

while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym[cur] = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym[cur])
    logging.debug(f" ym={ym[cur]}")
    ymt.append(np.array(ym[(cur-lag) % size]).T)
    cur = (cur+1) % size

    #real-time update
    Nsim = len(ymt)
    xdata = range(Nsim)
    
    #extract columns and update lines directly with lagged data
    line1.set_data(xdata, [x[0].item() for x in ymt])
    line2.set_data(xdata, [x[1].item() for x in ymt])
    
    for ax in (ax1, ax2):
        ax.relim()
        ax.autoscale_view()

    plt.pause(0.001) # Render update

logging.info(f"retry={concore.retrycount}")

#################

# Final Save & cleanup
plt.ioff()
plt.savefig("hrmap.pdf")
plt.show()
