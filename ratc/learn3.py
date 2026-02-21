import concore
import numpy as np
import matplotlib.pyplot as plt
import time

GENERATE_PLOT = 1
concore.delay = 0.002
concore.simtime = 0

fout=open(concore.outpath+'1/history.txt','w')
fout2=open('historyfull.txt','a+')
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
u = concore.initval(init_simtime_u)
ym = concore.initval(init_simtime_ym)
ut = (concore.maxtime+1)*[np.array(u).T]
ymt = (concore.maxtime+1)*[np.array(ym).T]

# --- LIVE PLOT SETUP ---
if GENERATE_PLOT == 1:
    plt.ion() # Enable interactive mode
    
    # 1. Setup stim figure (Inputs)
    fig_u, axs_u = plt.subplots(3, 2)
    lines_u = []
    labels_u = ['Pw1 (s)', 'Pf1 (Hz)', 'Pw2 (s)', 'Pf2 (Hz)', 'Pw3 (s)', 'Pf3 (Hz)']
    for i, ax in enumerate(axs_u.flat):
        line, = ax.plot([], [])
        ax.set_ylabel(labels_u[i])
        if i >= 4: ax.set_xlabel('Learn Cycles')
        lines_u.append((ax, line))
    fig_u.tight_layout()

    # 2. Setup hrmap figure (Outputs)
    fig_ym, (ax_map, ax_hr) = plt.subplots(2, 1)
    line_map, = ax_map.plot([], [], label='Learn MAP')
    ax_map.set_ylabel('MAP (mmHg)')
    ax_map.legend(loc=0)
    
    line_hr, = ax_hr.plot([], [], label='Learn HR')
    ax_hr.set_xlabel('Cycles')
    ax_hr.set_ylabel('HR (bpm)')
    ax_hr.legend(loc=0)
# ------------------------

while(concore.simtime<concore.maxtime-1):
    while concore.unchanged():
        u = concore.read(concore.iport["VCY"],"u",init_simtime_u)
    
    current_idx = int(concore.simtime)
    ut[current_idx] = np.array(u).T
    
    while concore.unchanged():
        ym = concore.read(concore.iport["VPY"],"ym",init_simtime_ym)
    ymt[current_idx] = np.array(ym).T
    
    # --- LIVE UPDATE ---
    if GENERATE_PLOT == 1:
        xdata = range(current_idx + 1)
        
        # Update Inputs (slice up to current_idx)
        for i, (ax, line) in enumerate(lines_u):
            line.set_data(xdata, [x[i].item() for x in ut[:current_idx + 1]])
            ax.relim()
            ax.autoscale_view()
            
        # Update Outputs (slice up to current_idx)
        line_map.set_data(xdata, [x[0].item() for x in ymt[:current_idx + 1]])
        line_hr.set_data(xdata, [x[1].item() for x in ymt[:current_idx + 1]])
        for ax in (ax_map, ax_hr):
            ax.relim()
            ax.autoscale_view()

        plt.pause(0.001) # Render updates
    # -------------------

print("retry="+str(concore.retrycount))

for i in range(2,concore.maxtime):
    fout.write(str(ymt[i-2])+str(ymt[i-1])+str(ut[i])+" "+str(ymt[i])+'\n')
    fout2.write(str(ymt[i-2])+str(ymt[i-1])+str(ut[i])+" "+str(ymt[i])+'\n')
fout.close()
fout2.close()

# --- FINAL SAVE & CLEANUP ---
if GENERATE_PLOT == 1:
    plt.ioff()
    fig_u.savefig("stim.pdf")
    fig_ym.savefig("hrmap.pdf")
    plt.show() # Keep plot open at the end