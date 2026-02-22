import concore
import logging
import numpy as np
import matplotlib.pyplot as plt
import time
logging.info("plot ym")

concore.delay = 0.02
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"
ymt = []
ym = concore.initval(init_simtime_ym)

# 1. Fetch 'realtime' parameter passed from terminal (defaults to False)
realtime = concore.tryparam('realtime', False)

# DEBUG: Check if the parameter was successfully caught
logging.info(f"--- Realtime mode is set to: {realtime} ---")

# 2. Set up interactive plot before the loop if realtime is True
if realtime:
    plt.ion() # Turn on interactive mode
    fig, ax1 = plt.subplots(1, 1)
    line1, = ax1.plot([], [])
    
    ax1.set_ylabel('ym')
    ax1.legend(['ym'], loc=0)
    ax1.set_xlabel('Cycles')
    plt.show(block=False) # Ensure it does not block the script

while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym)
    logging.debug(f" ym={ym}")
    ymt.append(np.array(ym).T)
    
    # 3. Update the plot iteratively during the simulation
    if realtime:
        ym1 = [x[0].item() for x in ymt]
        x_data = range(len(ym1))
        
        line1.set_data(x_data, ym1)
        
        ax1.relim()
        ax1.autoscale_view()
        
        # Force the GUI to draw the new data and flush UI events
        fig.canvas.draw()
        fig.canvas.flush_events()

logging.info(f"retry={concore.retrycount}")

#################

# 4. Finalize plotting
if realtime:
    plt.ioff() # Turn off interactive mode so the plot stays open at the end
    plt.savefig("ym.pdf")
    plt.show()
else:
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