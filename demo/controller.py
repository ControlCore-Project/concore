import numpy as np
import concore

ysp = 3.0

#//controller function//
def controller(ym): 
  if ym[0] < ysp:
     return 1.01 * ym
  else:
     return 0.9 * ym

#//main//
concore.default_maxtime(150) ##maps to-- for i in range(0,150):
concore.delay = 0.02

#//initial values-- transforms to string including the simtime as the 0th entry in the list//
# u = np.array([[0.0]])
# ym = np.array([[0.0]]) 
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
    print(str(concore.simtime) + ". u="+str(u) + "ym="+str(ym));
    concore.write(1,"u",list(u.T[0]),delta=0)

print("retry="+str(concore.retrycount))


#//main//
#for i in range(0,150):
#  u = controller(ym)
#  print('u='+repr(u)+' ym='+repr(ym))    


# ./dhg
# python3 mkconcore.py demo/sample.graphml demo/ demo-study macos
# files in main_program.dir (main_program.py) are copied. // controller2.py --> controller2.dir 
# ubuntu, windows, (posix), docker
# mkconcore 21-11-23
#concore path:      .
#graphml input:     demo/sample.graphml
#source directory:  demo/
#output directory:  demo-study
#control core type: posix
#treat .m as octave:False
#MCR path:          /opt/matlab/MATLAB_Runtime_R2021a_Update_5/v910

# cd demo-study/
# ./build
#./clear
#./maxtime 300
# ./debug

### For Docker
# Dockerfile.pm2 created in the demo folder by copying and editing concore20/Dockerfile.py.
# add the below:::
# RUN pip install tensorflow
# CMD ["python", "-i", "pm2.py"]

# python3 mkconcore.py demo/sample.graphml demo/ demo-study docker
# ./build
# ./run // for docker
# ./stop
# ./clear