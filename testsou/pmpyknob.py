import concore

concore.delay = 0.01
#Nsim = 100
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
init_simtime_knob = "[0.0, 10000]"
try:
    uport = concore.iport["VCY"]
    knobport = concore.iport["KNOB"]
except:
    uport = 1
    knobport = 1

ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(uport,"u",init_simtime_u)
        knob = concore.read(knobport,"knob",init_simtime_knob)
    ym[0]  = u[0]+knob[0]
    print("ym="+str(ym[0])+" u="+str(u[0]));
    concore.write(1,"ym",ym,delta=1)
#concore.write(1,"ym",init_simtime_ym)
print("retry="+str(concore.retrycount))
