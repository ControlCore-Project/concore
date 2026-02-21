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

plt.ion() # enable interactive mode
fig, ax = plt.subplots(1, 1)

line, = ax.plot([], [])
ax.set_ylabel('ym')
ax.legend(['ym'], loc=0)
ax.set_xlabel('Cycles')

ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    concore.write(1,"ym",ym)
    print("ym="+str(ym))
    ymt.append(np.array(ym).T)

    #real-time update
    Nsim = len(ymt)
    
    #update line dynamically
    line.set_data(range(Nsim), [x[0].item() for x in ymt])
    ax.relim()
    ax.autoscale_view()
    
    plt.pause(0.001) # Render update

print("retry="+str(concore.retrycount))

#################

# Final Save & cleanup
plt.ioff()
plt.savefig("ym.pdf")
plt.show()
