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
u = concore.initval(init_simtime_u)

# --- Real-time plotting setup ---
realtime = concore.tryparam('realtime', False)
if realtime:
    plt.ion()
    fig, axs = plt.subplots(3, 2, figsize=(8, 6))
    lines = [ax.plot([], [])[0] for ax in axs.flat]
    ylabels = ['Pw1 (s)', 'Pf1 (Hz)', 'Pw2 (s)', 'Pf2 (Hz)', 'Pw3 (s)', 'Pf3 (Hz)']
    
    for ax, ylab in zip(axs.flat, ylabels):
        ax.set_ylabel(ylab)
    axs[2, 0].set_xlabel('Cycles')
    axs[2, 1].set_xlabel('Cycles')
    plt.tight_layout()
    plt.show(block=False)
# --------------------------------

while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    concore.write(1,"u",u)
    logging.debug(f"u={u}")
    ut.append(np.array(u).T)
    
    # --- Real-time plot update ---
    if realtime and len(u) >= 6:
        for i in range(6):
            lines[i].set_data(range(len(ut)), [x[i].item() for x in ut])
            axs.flat[i].relim()
            axs.flat[i].autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()
    # -----------------------------

logging.info(f"retry={concore.retrycount}")

#################

# Finalize rendering
if realtime:
    plt.ioff()
else:
    # Original static plotting logic
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
    plt.tight_layout()

# Save and show for both modes
plt.savefig("stim.pdf")
plt.show()


