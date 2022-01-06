import concore

concore.delay = 0.01
Nsim = 100
init_simtime_u = "[0.0,0.0,0.0]"
init_simtime_ym = "[0.0,0.0,0.0]"

u = concore.initval(init_simtime_u)
while(concore.simtime<Nsim):
    while concore.unchanged():
        ym = concore.read(concore.iport["VPZ"],"ym",init_simtime_ym)
    u[0]  = ym[0]+1
    print("ym="+str(ym[0])+" u="+str(u[0]));
    concore.write(1,"u",u);
concore.write(concore.oport["VCZ"],"u",init_simtime_u)
print("retry="+str(concore.retrycount))
