import numpy as np
import concore
setpoint = 67.5
Kp = 0.1
Ki = 0.01
Kd = 0.01
dT = 0.1
global Prev_Error, I
Prev_Error = 0
I = 0


def  pid_controller(ym):
    global Prev_Error, I
    Error = setpoint- ym[0]
    P = Error
    I = I + Error*dT 
    D = (Error - Prev_Error )/dT	
    amp = Kp*P + Ki*I + Kd*D
    Prev_Error = Error      
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
    
    ustar =  pid_controller(ym)
    
    print(str(concore.simtime) + " u="+str(ustar) + "ym="+str(ym))
    concore.write(1,"u",list(ustar),delta=0)

