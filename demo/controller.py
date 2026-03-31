import numpy as np
import concore

ysp = 3.0

# controller function
def controller(ym): 
  if ym[0] < ysp:
     return 1.01 * ym
  else:
     return 0.9 * ym

# main
concore.default_maxtime(150)
concore.delay = 0.02

# initial values -- transforms to string including the simtime as the 0th entry in the list
init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

u = np.array([concore.initval(init_simtime_u)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    ym = np.array([ym]).T
    #####
    u = controller(ym)
    #####
    print(str(concore.simtime) + ". u="+str(u) + "ym="+str(ym))
    # Convert numpy arrays to standard Python lists for writing
    u_list = [float(x) for x in u.T[0]]
    concore.write(1,"u",u_list,delta=0)

print("retry="+str(concore.retrycount))
