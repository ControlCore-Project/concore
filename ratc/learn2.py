import concore
import numpy as np
import matplotlib.pyplot as plt
import time
GENERATE_PLOT = 0
fout=open(concore.outpath+'1/history.txt','w')
fout2=open('historyfull.txt','a+')
concore.delay = 0.002
concore.default_maxtime(150)
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
u = concore.initval(init_simtime_u)
ym = concore.initval(init_simtime_ym)
ut = (concore.maxtime+1)*[np.array(u).T]
ymt = (concore.maxtime+1)*[np.array(ym).T]
oldsimtime = concore.simtime
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(concore.iport["VCY"],"u",init_simtime_u)
        ym = concore.read(concore.iport["VPY"],"ym",init_simtime_ym)
    if concore.simtime > oldsimtime:
        ut[int(concore.simtime)] = np.array(u).T
        ymt[int(concore.simtime)] = np.array(ym).T
        #fout.write(str(u)+str(ym)+'\n')
        #fout2.write(str(u)+str(ym)+'\n')
    oldsimtime = concore.simtime
print("retry="+str(concore.retrycount))

for i in range(2,concore.maxtime):
    fout.write(str(ymt[i-2])+str(ymt[i-1])+str(ut[i])+" "+str(ymt[i])+'\n')
    fout2.write(str(ymt[i-2])+str(ymt[i-1])+str(ut[i])+" "+str(ymt[i])+'\n')
fout.close()
fout2.close()

#################
# plot inputs and outputs

if GENERATE_PLOT == 1:
 u1 = [x[0].item() for x in ut]
 u2 = [x[1].item() for x in ut]
 u3 = [x[2].item() for x in ut]
 u4 = [x[3].item() for x in ut]
 u5 = [x[4].item() for x in ut]
 u6 = [x[5].item() for x in ut]
 Nsim = len(u1)
 plt.figure()
 plt.subplot(321)
 plt.plot(range(Nsim), u1)
 plt.ylabel('Pw1 (s)')
 plt.subplot(322)
 plt.plot(range(Nsim), u2)
 plt.ylabel('Pf1 (Hz)')
 plt.subplot(323)
 plt.plot(range(Nsim), u3)
 plt.xlabel('Learn Cycles')
 plt.ylabel('Pw2 (s)')
 plt.subplot(324)
 plt.plot(range(Nsim), u4)
 plt.ylabel('Pf2 (Hz)')
 plt.subplot(325)
 plt.plot(range(Nsim), u5)
 plt.ylabel('Pw3 (s)')
 plt.subplot(326)
 plt.plot(range(Nsim), u6)
 plt.xlabel('Learn Cycles')
 plt.ylabel('Pf3 (Hz)')
 plt.savefig("stim.pdf")
 plt.tight_layout()

 ym1 = [x[0].item() for x in ymt]
 ym2 = [x[1].item() for x in ymt]
 Nsim = len(ym1)
 plt.figure()
 plt.subplot(211)
 plt.plot(range(Nsim), ym1)
 plt.ylabel('MAP (mmHg)')
 plt.legend(['Learn MAP'], loc=0)
 plt.subplot(212)
 plt.plot(range(Nsim), ym2)
 plt.xlabel('Cycles')
 plt.ylabel('HR (bpm)')
 plt.legend(['Learn HR'], loc=0)
 plt.savefig("hrmap.pdf")
 plt.show()
