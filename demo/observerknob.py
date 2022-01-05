import concore
import time
concore.delay = 0.01

concore.default_maxtime(150)
init_simtime_ym = "[0.0, 0.0]"
init_simtime_knob = "[0.0, 3.0]"
knob = concore.initval(init_simtime_knob)

while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    if (concore.simtime > concore.maxtime/4):
        knob[0] = 0.5
        if (concore.simtime > concore.maxtime/2):
            knob[0] = 1.0
        concore.write(1,"knob",knob);
        print("time="+str(concore.simtime)+" knob="+str(knob[0]))
 
print("retry="+str(concore.retrycount))
