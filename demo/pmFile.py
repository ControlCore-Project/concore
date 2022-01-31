import concore
import numpy as np

#//pm function//
def pm(u):
  return u + 0.01

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
    u = np.array([u]).T
    #####
    try:
        infile = open(concore.inpath+"1/file.txt")
        print(infile.read())
        infile.close()
    except:
        print("no file.txt yet")
    ym = pm(u)
    #####
    print(str(concore.simtime) + ". u="+str(u) + "ym="+str(ym));
    concore.write(1,"ym",list(ym.T[0]),delta=1)

print("retry="+str(concore.retrycount))


#// main-- to begin with//
#for i in range(0,150):
#  ym = pm(u)
#  print('u='+repr(u)+' ym='+repr(ym))
