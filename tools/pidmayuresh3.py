import numpy as np
import math
import concore
dT = 0.1

sp = concore.tryparam('sp', 67.5)
Kp = concore.tryparam('Kp', 0.075)
Ki = concore.tryparam('Ki', 0.02)
Kd = concore.tryparam('Kd', 0.005)
freq = concore.tryparam('freq',30)
sigout = concore.tryparam('sigout',True)
cin = concore.tryparam('cin', 'hr')

def  pid_controller(state, ym, sp, Kp, Ki, Kd, sigout, cin, low, up):
    Prev_Error = state[0]
    I = state[1]
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
        amp = (up-low)/(1.0 + math.exp(amp)) + low
    state = [Prev_Error, I]
    return (state, amp)


concore.default_maxtime(150)
concore.delay = 0.02
init_simtime_ym = "[0.0, 70.0,91]"
ym = np.array(concore.initval(init_simtime_ym))
state = [0.0, 0.0]
print("Mayuresh's PID controller: sp is "+str(sp))
print(concore.params)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    ym = np.array(ym)
    (state,amp) =  pid_controller(state,ym,sp,Kp,Ki,Kd,sigout,cin,0,3)
    u = np.array([amp,freq])    
    print(str(concore.simtime) + " u="+str(u) + "ym="+str(ym))
    concore.write(1,"u",list(u),delta=0)



