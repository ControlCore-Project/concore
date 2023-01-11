import numpy as np
import concore
setpoint = 67.5
setpointF = 75.0
KpF = 0.1
KiF = 0.01
KdF = 0.01
Kp = 0.1
Ki = 0.01
Kd = 0.01
dT = 0.1
global Prev_Error, I
Prev_Error = 0
I = 0
global Prev_ErrorF, IF
Prev_ErrorF = 0
IF = 0


def  pid_controller(ym):
    global Prev_Error, I
    global Prev_ErrorF, IF
    Error = setpoint- ym[1]
    dT = 60.0/ym[1]
    P = Error
    I = I + Error*dT 
    D = (Error - Prev_Error )/dT	
    amp = Kp*P + Ki*I + Kd*D
    if amp>3:
       amp = 3
    if amp<0:
       amp = 0
    Prev_Error = Error      

    ErrorF = setpointF- ym[0]
    PF = ErrorF
    IF = IF + ErrorF*dT 
    DF = (ErrorF - Prev_ErrorF )/dT	
    freq= KpF*PF + KiF*IF + KdF*DF
    if freq>30:
       freq = 30
    if freq<10:
       freq = 10
    Prev_ErrorF = ErrorF      
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

