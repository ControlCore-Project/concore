#pmcvxpymat
import concore
import numpy as np
import scipy.io as sio
from scipy import optimize
from numpy.linalg import inv
import matplotlib.pyplot as plt

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

def Plant(u, x, X):
    #print('before x='+str(x.T))
    #print('before u='+str(u.T))
    newx = np.dot(X['A'], x) + np.dot(X['B'], u)
    newy = np.dot(X['C'], x) + np.dot(X['D'], u)
    #print('after x='+str(x.T))
    #print('after y='+str(y.T))
    return newx, newy

# convert data from matlab to python
X = Get_MPC_Constants()              # model and controller constants
# initialize model constant and variables
xm = X['x0']                         # initial condition of plant
u = X['us']                          # initial input
print("us")
print(u)
# initialize controller constant and variables
#Nsim =  150                          # number of simulation cycles
concore.default_maxtime(150)

# set list to record inputs and outputs for plotting
ut = []
ymt = []

X = Get_MPC_Constants()
print("initial plant")
print(X['x0'])
print("initial input");
print(X['us'])


concore.delay = 0.02
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

# --- LIVE PLOT SETUP ---
plt.ion() # Enable interactive mode

# 1. Setup hrmap figure (Outputs)
fig_ym, (ax_map, ax_hr) = plt.subplots(2, 1)
line_map_m, = ax_map.plot([], [], label='MAPm')
ax_map.set_ylabel('MAP (mmHg)')
ax_map.legend(loc=0)

line_hr_m, = ax_hr.plot([], [], label='HRm')
ax_hr.set_xlabel('Cycles')
ax_hr.set_ylabel('HR (bpm)')
ax_hr.legend(loc=0)

# 2. Setup stim figure (Inputs)
fig_u, axs_u = plt.subplots(3, 2)
lines_u = []
labels_u = ['Pw1 (s)', 'Pf1 (Hz)', 'Pw2 (s)', 'Pf2 (Hz)', 'Pw3 (s)', 'Pf3 (Hz)']
for i, ax in enumerate(axs_u.flat):
    line, = ax.plot([], [])
    ax.set_ylabel(labels_u[i])
    if i >= 4: ax.set_xlabel('Cycles')
    lines_u.append((ax, line))
fig_u.tight_layout()
# ------------------------

ym = np.array([concore.initval(init_simtime_ym)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    u = np.array([u]).T
    print(u)
    #####
    xm, ym = Plant(u, xm, X)
    
    # Store history for plotting
    ut.append(list(u.T[0]))
    ymt.append(list(ym.T[0]))
    #####
    
    # --- LIVE UPDATE ---
    Nsim = len(ymt)
    xdata = range(Nsim)
    
    # Update Outputs (ym)
    line_map_m.set_data(xdata, [x[0] for x in ymt])
    line_hr_m.set_data(xdata, [x[1] for x in ymt])
    for ax in (ax_map, ax_hr):
        ax.relim()
        ax.autoscale_view()
        
    # Update Inputs (u)
    for i, (ax, line) in enumerate(lines_u):
        line.set_data(xdata, [x[i] for x in ut])
        ax.relim()
        ax.autoscale_view()

    plt.pause(0.001) # Render updates
    # -------------------
    
    print("ym="+str(ym)+" u="+str(u));
    concore.write(1,"ym",list(ym.T[0]),delta=1)

print("retry="+str(concore.retrycount))

# --- FINAL CLEANUP ---
plt.ioff()
plt.show() # Keep plot open at the end