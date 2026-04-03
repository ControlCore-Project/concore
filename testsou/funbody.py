import concore
print("funbody")

concore.delay = 0.07
concore.simtime = 0
concore.default_maxtime(100)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

u = concore.initval(init_simtime_u)
ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(concore.iport['U1'],"u",init_simtime_u)
    concore.write(concore.oport['U2'],"u",u)
    print(u)
    old2 = float(concore.simtime)
    while concore.unchanged() or concore.simtime <= old2:
        ym = concore.read(concore.iport['Y2'],"ym",init_simtime_ym)
    concore.write(concore.oport['Y1'],"ym",ym)
    print("funbody u="+str(u)+" ym="+str(ym)+" time="+str(concore.simtime))
print("retry="+str(concore.retrycount))
