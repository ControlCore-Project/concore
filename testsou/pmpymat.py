import concore

concore.delay = 0.01
Nsim = 100
init_simtime_u = "[0.0,0.0,0.0]"
init_simtime_ym = "[0.0,0.0,0.0]"

ym = concore.initval(init_simtime_ym)
while(concore.simtime<Nsim):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    ym[0]  = u[0]+10000
    print("ym="+str(ym[0])+" u="+str(u[0]));
    concore.write(1,"ym",ym,delta=1)
concore.write(1,"ym",init_simtime_ym)
print("retry="+str(concore.retrycount))
