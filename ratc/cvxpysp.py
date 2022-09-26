#control cvxpymatcore
import concore
import numpy as np
import scipy.io as sio
from scipy import optimize
from numpy.linalg import inv
import matplotlib.pyplot as plt
import cvxopt
from cvxopt import solvers
import time

GENERATE_PLOT = 1

def Get_MPC_Constants():
    MPC_data = sio.loadmat('MPC_data.mat', struct_as_record = False, squeeze_me = True)
    Data = MPC_data['Data']
    A = np.array(Data.op1.A)
    B = np.array(Data.op1.B)
    C = np.array(Data.op1.C)
    D = np.array(Data.op1.D)
    x0 = np.array(Data.op1.x0)
    x0 = x0.reshape(x0.size, 1)
    xs = np.array(Data.op1.xs)
    xs = xs.reshape(xs.size, 1)
    us = np.array(Data.op1.us)
    us = us.reshape(us.size, 1)
    ysp = np.array(Data.op1.ysp)
    ysp = ysp.reshape(ysp.size, 1)
    Us = np.array(Data.op1.Us)
    Us = Us.reshape(Us.size, 1)
    Ys = np.array(Data.op1.Ys)
    Ys = Ys.reshape(Ys.size, 1)
    alpha = np.array(Data.op1.alpha)
    beta = np.array(Data.op1.beta)
    gamma = np.array(Data.op1.gamma)
    V = np.array(Data.op1.V)
    G = np.array(Data.op1.G)
    W = np.array(Data.op1.W)
    Z = np.array(Data.op1.Z)
    J = np.array(Data.op1.J)
    Nu = np.array(Data.input.Nu)
    Nx = np.array(Data.input.Nx)
    Ny = np.array(Data.input.Ny)
    Umax = np.array(Data.input.Umax)
    Umax = Umax.reshape(Umax.size, 1)
    Umin = np.array(Data.input.Umin)
    Umin = Umin.reshape(Umin.size, 1)
    Ymax = np.array(Data.output.Ymax)
    Ymax = Ymax.reshape(Ymax.size, 1)
    Ymin = np.array(Data.output.Ymin)
    Ymin = Ymin.reshape(Ymin.size, 1)
    Np = np.array(Data.input.Np)
    Pd = np.array(Data.input.Pd)
    Rd = np.array(Data.input.Rd)
    Qd = np.array(Data.input.Qd)

    X = {'A': A, 'B': B, 'C': C, 'D': D, \
         'Nu': Nu, 'Nx': Nx, 'Ny': Ny, 'Np': Np, \
         'x0': x0, 'us': us, 'xs': xs, 'ysp': ysp, 'Us': Us, 'Ys': Ys, \
         'Pd': Pd, 'Rd': Rd, 'Qd': Qd, \
         'alpha': alpha, 'beta': beta, 'gamma': gamma, 'W': W, 'V': V, 'G': G, 'Z': Z, 'J': J,\
         'Umax': Umax, 'Umin': Umin, 'Ymax': Ymax, 'Ymin': Ymin}
    return X

def MPC(x0, u, y, Pd, X):
    # Substract steady state values of inputs and outputs
    yp = y - X['ysp']
    up = u - X['us']
    # Time-varying Kalman filter
    M = np.dot(np.dot(Pd, X['C'].T), inv(np.dot(np.dot(X['C'], Pd), X['C'].T) + X['Rd']))
    x_0 = x0 + np.dot(M, yp - np.dot(X['C'], x0) - np.dot(X['D'], u))
    Pd = np.dot(np.dot(X['A'], Pd - np.dot(np.dot(M, X['C']), Pd)), X['A'].T) + X['Qd']
    # Construct QP matrices
    H = np.dot(np.dot(X['W'].T, X['alpha']), X['W']) + X['beta'] + np.dot(np.dot(X['Z'].T, X['gamma']), X['Z'])
    H = (H + H.T)/2
    H = cvxopt.matrix(H)
    f = np.dot(np.dot(np.dot(X['W'].T, X['alpha'].T), X['V']), x_0)
    f = cvxopt.matrix(f)
    A = np.concatenate((np.eye(X['Nu']*(X['Np'] - 1)), -np.eye(X['Nu']*(X['Np'] - 1)),  \
        np.dot(X['G'], X['W']) + X['J'], -np.dot(X['G'], X['W']) - X['J']), axis = 0)
    A = cvxopt.matrix(A)
    b = np.concatenate((X['Umax'] - X['Us'],-(X['Umin'] - X['Us']), \
        X['Ymax'] - X['Ys']- np.dot(np.dot(X['G'], X['V']), x_0), \
        -(X['Ymin'] - X['Ys']- np.dot(np.dot(X['G'], X['V']), x_0))), axis = 0)
    b = cvxopt.matrix(b)
    # Solve quadratic program
    solvers.options['show_progress'] = False
    # Apply solution if QP solved successful
    sol = solvers.qp(H, f, A, b)
    if sol['status'] == 'optimal':
        U = sol['x']
        u = np.array(U[0:X['Nu']]).reshape(X['Nu'], 1) + X['us']
    else:
        u = u
    x0 = np.dot(X['A'], x_0) + np.dot(X['B'], up)
    # Return outputs
    return u, x0, Pd

X = Get_MPC_Constants()              # model and controller constants
try:
    MAPsp = concore.params['MAPsp']
except:
    MAPsp = X['ysp'][0] 
try:
    HRsp = concore.params['HRsp']
except:
    HRsp = X['ysp'][1] 
print("MAPsp="+str(MAPsp)+ " HRsp="+str(HRsp))
X['ysp'][0] = MAPsp 
X['ysp'][1] = HRsp 

print(X['A'])
# convert data from matlab to python
# initialize model constant and variables
#xm = X['x0']                         # initial condition of plant
u = X['us']                          # initial input
print("initial input")
print(X['us'])
# initialize controller constant and variables
#Nsim =  150                          # number of simulation cycles
concore.default_maxtime(150)
xc = np.zeros((X['Nx'], 1))          # initial conditon of state in MPC
Pd = X['Pd']                         # variance of initial state
# set list to record inputs and outputs
ut = []
ymt = []


concore.delay = 0.02
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
u = np.array([concore.initval(init_simtime_u)]).T
wallclock1 = time.perf_counter()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    ym = np.array([ym]).T
    #################
    ut.append(u)
    ymt.append(ym)
    u, xc, Pd = MPC(xc, u, ym, Pd, X)
    #################
    print("ym="+str(ym)+" u="+str(u));
    concore.write(1,"u",list(u.T[0]));
wallclock2 = time.perf_counter()
#concore.write(1,"u",init_simtime_u)
print("retry="+str(concore.retrycount))
print("time/iter="+str((wallclock2-wallclock1)/concore.maxtime))

if GENERATE_PLOT == 0:
    quit()

# plot inputs and outputs
ym1 = [x[0].item() for x in ymt]
ym2 = [x[1].item() for x in ymt]
u1 = [x[0].item() for x in ut]
u2 = [x[1].item() for x in ut]
u3 = [x[2].item() for x in ut]
u4 = [x[3].item() for x in ut]
u5 = [x[4].item() for x in ut]
u6 = [x[5].item() for x in ut]

Nsim = len(ym1)
plt.figure()
plt.subplot(211)
plt.plot(range(Nsim), ym1)
plt.plot(range(Nsim), np.tile(X['ysp'][0], Nsim))
plt.ylabel('MAP (mmHg)')
plt.legend(['MAPm', 'MAPsp'], loc=0)
plt.subplot(212)
plt.plot(range(Nsim), ym2)
plt.plot(range(Nsim), np.tile(X['ysp'][1], Nsim))
plt.xlabel('Cycles')
plt.ylabel('HR (bpm)')
plt.legend(['HRm', 'HRsp'], loc=0)
plt.savefig("hrmap.pdf")
#plt.tight_layout()

plt.figure()
plt.subplot(321)
plt.plot(range(Nsim), u1)
plt.ylabel('Pw1 (s)')
plt.subplot(322)
plt.plot(range(Nsim), u2)
plt.ylabel('Pf1 (Hz)')
plt.subplot(323)
plt.plot(range(Nsim), u3)
plt.xlabel('Cycles')
plt.ylabel('Pw2 (s)')
plt.subplot(324)
plt.plot(range(Nsim), u4)
plt.ylabel('Pf2 (Hz)')
plt.subplot(325)
plt.plot(range(Nsim), u5)
plt.ylabel('Pw3 (s)')
plt.subplot(326)
plt.plot(range(Nsim), u6)
plt.xlabel('Cycles')
plt.ylabel('Pf3 (Hz)')
plt.savefig("stim.pdf")
plt.tight_layout()
plt.show()


