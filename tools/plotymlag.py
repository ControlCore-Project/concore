import concore
import logging
import numpy as np
import matplotlib.pyplot as plt
import time

size = 10
lag = concore.tryparam("lag", 0)
if lag >= size:
    logging.warning(
        "Requested lag (%d) exceeds buffer size (%d). Clamping to %d.",
        lag, size, size - 1
    )
    lag = size - 1
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

# --- Real-time plotting setup ---
realtime = concore.tryparam('realtime', False)
if realtime:
    plt.ion()
    fig, axs = plt.subplots(2, 1)
    lines = [ax.plot([], [])[0] for ax in axs]
    
    axs[0].set_ylabel('MAP (mmHg)')
    axs[0].legend(['MAP'], loc=0)
    
    axs[1].set_xlabel('Cycles ' + str(concore.params))
    axs[1].set_ylabel('HR (bpm)')
    axs[1].legend(['HR'], loc=0)
    plt.tight_layout()
    plt.show(block=False)
# --------------------------------

while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym[cur] = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym[cur])
    logging.debug(f" ym={ym[cur]}")
    ymt.append(np.array(ym[(cur-lag) % size]).T)
    cur = (cur+1) % size
    
    # --- Real-time plot update ---
    if realtime and len(ymt) > 0 and len(ymt[-1]) >= 2:
        for i in range(2):
            lines[i].set_data(range(len(ymt)), [x[i].item() for x in ymt])
            axs[i].relim()
            axs[i].autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()
    # -----------------------------

logging.info(f"retry={concore.retrycount}")

#################

# plot inputs and outputs
if realtime:
    plt.ioff()
else:
    # Original static plotting logic
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
    plt.tight_layout()

plt.savefig("hrmap.pdf")
plt.show()