import numpy as np
import concore


def controller(ym): 
  if ym[0] < ysp:
     return 1.01 * ym
  else:
     return 0.9 * ym

concore.default_maxtime(150) 
concore.delay = 0.02

init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"
init_simtime_knob = "[0.0, 3.0]"
try:
    ymport = concore.iport["PYM"]
    knobport = concore.iport["KNOB"]
except:
    ymport = 1
    knobport = 1

u = np.array([concore.initval(init_simtime_u)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(ymport,"ym",init_simtime_ym)
        knob = concore.read(knobport,"knob",init_simtime_knob)
    ysp = knob[0]
    ym = np.array([ym]).T
    #####
    u = controller(ym)
    #####
    print(str(concore.simtime) + ". u="+str(u) + "ym="+str(ym));
    concore.write(1,"u",list(u.T[0]),delta=0)

print("retry="+str(concore.retrycount))
