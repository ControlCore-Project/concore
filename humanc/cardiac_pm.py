import numpy as np
import pulsatile_model_functions as pmf
import healthy_params as K
import concore

#x0 = np.loadtxt('pulsatile_steady.txt')

rx0 =  np.concatenate((np.zeros(4),np.array([-0.25, 1, -0.25, 1]),np.zeros(20),np.array([K.theta0[8],K.Vulv,K.Vurv])))
dx0 = pmf.generate_historylist()
x0 = np.concatenate((rx0,dx0))


def cardiac_pm(x0,u):
    hr, mapp, x0 = pmf.healthy_pm(x0, u)
    
    return hr,mapp,x0

concore.default_maxtime(150)
concore.delay = 0.02
init_simtime_u = "[0.0, 0.0,0.0]"
init_simtime_ym = "[0.0, 70,0]"
ym = np.array([concore.initval(init_simtime_ym)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    u = np.array(u)

    hr,mapp,x0 = cardiac_pm(x0,u)
    
    dummy = np.array([hr,mapp])
    print(str(concore.simtime) + " u="+str(u) + "ym=" + str(dummy))
    concore.write(1,"ym",list(np.array([hr,mapp])),delta=1)


