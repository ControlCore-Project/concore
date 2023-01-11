import concore
print("funby")

concore.delay = 0.07
concore.default_maxtime(100)
init_simtime_ym = "[0.0, 0.0, 0.004]"

ym = concore.initval(init_simtime_ym)
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(concore.iport['Y2'],"ym",init_simtime_ym)
    concore.write(concore.oport['Y1'],"ym",ym)
    print("funby ym="+str(ym))
print("retry="+str(concore.retrycount))
