import numpy as np
import math
import concore
dT = 0.1
global freq
Prev_Error = 0
I = 0

sp = concore.tryparam('sp', 67.5)
Kp = concore.tryparam('Kp', 0.075)
Ki = concore.tryparam('Ki', 0.02)
Kd = concore.tryparam('Kd', 0.005)
freq = concore.tryparam('freq',30)
sigout = concore.tryparam('sigout',True)
cin = concore.tryparam('cin', 'hr')

def  pid_controller(Prev_Error, I, ym):
    global freq
    if cin == 'hr':
        Error = sp - ym[1]
    elif cin == 'map':
        Error = sp - ym[0]
    else:
        print('invalid control input '+cin)
        quit()
    P = Error
    I = I + Error*dT 
    D = (Error - Prev_Error )/dT	
    amp = Kp*P + Ki*I + Kd*D
    Prev_Error = Error      
    if sigout:
        amp = 3.0/(1.0 + math.exp(amp))
    ustar = np.array([amp,freq])    
    return (Prev_Error, I, ustar)


concore.default_maxtime(150)
concore.delay = 0.02
init_simtime_ym = "[0.0, 70.0,91]"
ym = np.array(concore.initval(init_simtime_ym))
print("Mayuresh's PID controller: sp is "+str(sp))
print(concore.params)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    ym = np.array(ym)
    (Prev_Error, I, ustar) =  pid_controller(Prev_Error, I, ym)
    print(str(concore.simtime) + " u="+str(ustar) + "ym="+str(ym))
    concore.write(1,"u",list(ustar),delta=0)



