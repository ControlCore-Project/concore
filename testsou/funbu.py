import concore
print("funbu")

concore.delay = 0.07
concore.default_maxtime(100)
init_simtime_u = "[0.0, 0.0, 0.003]"
init_simtime_ym = "[0.0, 0.0, 0.004]"

u = concore.initval(init_simtime_u)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(concore.iport['U1'],"u",init_simtime_u)
    concore.write(concore.oport['U2'],"u",u)
    print("funbu u="+str(u))
print("retry="+str(concore.retrycount))
