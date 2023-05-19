import concore
#from hardware.util_functions import accurate_delay
import time
import threading

global uglobal
uglobal = 0.5
try:
  PULSE_WIDTH = concore.params['pw']
except:
  PULSE_WIDTH = 10

def pwm():
    while(True):
        ulocal = uglobal
        if ulocal < 0.0:
            ulocal = 0.0
        if ulocal > 1.0:
            ulocal = 1.0
        print("+")
        time.sleep(PULSE_WIDTH*ulocal)
        print("-")
        time.sleep(PULSE_WIDTH*(1.0-ulocal))

pwm_thread = threading.Thread(target=pwm, daemon=True)

concore.delay = 0.001
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

ym = concore.initval(init_simtime_ym)

pwm_thread.start()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    uglobal = float(u[0])
    ym[0]  = u[0]*100
    print("")
    print("ym="+str(ym[0])+" u="+str(u[0]));
    concore.write(1,"ym",ym,delta=1)
print("retry="+str(concore.retrycount))
