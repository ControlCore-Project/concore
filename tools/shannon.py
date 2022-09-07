import numpy as np
import concore
setpoint = 67.5


def bangbang_controller(ym):
    amp = 0
    if ym[0]>setpoint +2.5:
        amp = 3
    elif ym[0]<setpoint -2.5:
        amp = 1
	    
     
    ustar = np.array([amp,30])    
    return ustar


concore.default_maxtime(150)
concore.delay = 0.02
init_simtime_u = "[0.0, 0.0,0.0]"
init_simtime_ym = "[0.0, 70.0,91]"
u = np.array([concore.initval(init_simtime_u)]).T
print("Shannon's PID controller: setpoint is "+str(setpoint))
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    ym = np.array(ym)
    
    ustar = bangbang_controller(ym)
    
    print(str(concore.simtime) + " u="+str(ustar) + "ym="+str(ym))
    concore.write(1,"u",list(ustar),delta=0)
