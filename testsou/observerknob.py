import concore
import time
concore.delay = 0.01

init_simtime_ym = "[0.0, 0.0, 0.0]"
init_simtime_knob = "[0.0, 10000.0]"
knob = concore.initval(init_simtime_knob)

while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    if (concore.simtime > concore.maxtime/2):
        knob[0] = 20000.0
        concore.write(1,"knob",knob);
        print("time="+str(concore.simtime)+" knob="+str(knob[0]))
 
print("retry="+str(concore.retrycount))
