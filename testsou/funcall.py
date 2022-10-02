import concore
import concore2
print("funcall")

concore.delay = 0.07
concore2.delay = 0.07
concore2.inpath = concore.inpath
concore2.outpath = concore.outpath
concore2.simtime = 0
concore.default_maxtime(100)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(concore.iport['U'],"u",init_simtime_u)
    concore2.write(concore.oport['U1'],"u",u)
    old2 = concore2.simtime
    while concore2.simtime<=old2:
        ym = concore2.read(concore.iport['Y1'],"ym",init_simtime_ym)
    concore.write(concore.oport['Y'],"ym",ym)
    print("funcall u="+str(u)+" ym="+str(ym)+" time="+str(concore2.simtime))
print("retry="+str(concore.retrycount))
