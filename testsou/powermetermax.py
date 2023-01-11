#CW
import concore
import concore2
import time
print("powermeter")

concore.delay = 0.07
concore2.delay = 0.07
concore2.inpath = concore.inpath
concore2.outpath = concore.outpath
concore2.simtime = 0
#Nsim = 100
concore.default_maxtime(100)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
energy = 0

ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(concore.iport['VC'],"u",init_simtime_u)
    concore2.write(concore.oport['VXP'],"u",u)
    while concore2.unchanged():
        ym = concore2.read(concore.iport['VP'],"ym",init_simtime_ym)
    concore.write(concore.oport['VXC'],"ym",ym)
    print("powermeter u="+str(u)+" ym="+str(ym))
print("retry="+str(concore.retrycount))
