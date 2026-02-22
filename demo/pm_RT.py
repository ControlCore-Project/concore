import concore
import numpy as np
import tensorflow as tf

#//pm function//
def pm(u,oldstate):
  newresult = u + 0.01
  newstate = 0.5*oldstate + 0.5*newresult
  return newstate,newresult 

pmstate = tf.convert_to_tensor(np.array([[4.0]]))
u = tf.convert_to_tensor(np.array([[0.0]]))

#//main//

concore.default_maxtime(150) ##maps to-- for i in range(0,150):
concore.delay = 0.02

#//initial values-- transforms to string including the simtime as the 0th entry in the list//
# u = np.array([[0.0]])
# ym = np.array([[0.0]]) 
init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

ym = np.array([concore.initval(init_simtime_ym)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)

    ### Added lines    
    u = tf.convert_to_tensor(np.array(u))
    pmstate,ym = pm(pmstate,u)
    ym = np.array(np.array(ym))
    ####

    print(str(concore.simtime) + ". u="+str(u) + "ym="+str(ym));
    concore.write(1,"ym",list(ym.T[0]),delta=1)

print("retry="+str(concore.retrycount))


#// main-- to begin with//
#for i in range(0,150):
#  ym = pm(u)
#  print('u='+repr(u)+' ym='+repr(ym))
