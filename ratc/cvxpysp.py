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

concore.default_maxtime(150)
xc = np.zeros((X['Nx'], 1))          # initial conditon of state in MPC
Pd = X['Pd']                         # variance of initial state

# set list to record inputs and outputs
ut = []
ymt = []


concore.delay = 0.02
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

# --- LIVE PLOT SETUP (Moved from bottom) ---
if GENERATE_PLOT == 1:
    plt.ion() # Enable interactive mode
    
    # 1. Setup hrmap figure (Outputs & Setpoints)
    fig_ym, (ax_map, ax_hr) = plt.subplots(2, 1)
    line_map_m, = ax_map.plot([], [], label='MAPm')
    line_map_sp, = ax_map.plot([], [], label='MAPsp')
    ax_map.set_ylabel('MAP (mmHg)')
    ax_map.legend(loc=0)
    
    line_hr_m, = ax_hr.plot([], [], label='HRm')
    line_hr_sp, = ax_hr.plot([], [], label='HRsp')
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
# -------------------------------------------

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

    # --- LIVE UPDATE ---
    if GENERATE_PLOT == 1:
        Nsim = len(ymt)
        xdata = range(Nsim)
        
        # Update hrmap figure (Outputs & Setpoints)
        line_map_m.set_data(xdata, [x[0].item() for x in ymt])
        line_map_sp.set_data(xdata, np.tile(X['ysp'][0], Nsim))
        line_hr_m.set_data(xdata, [x[1].item() for x in ymt])
        line_hr_sp.set_data(xdata, np.tile(X['ysp'][1], Nsim))
        
        for ax in (ax_map, ax_hr):
            ax.relim()
            ax.autoscale_view()
            
        # Update stim figure (Inputs)
        for i, (ax, line) in enumerate(lines_u):
            line.set_data(xdata, [x[i].item() for x in ut])
            ax.relim()
            ax.autoscale_view()

        plt.pause(0.001) # Render updates
    # -------------------

    print("ym="+str(ym)+" u="+str(u));
    concore.write(1,"u",list(u.T[0]));
    
wallclock2 = time.perf_counter()
#concore.write(1,"u",init_simtime_u)
print("retry="+str(concore.retrycount))
print("time/iter="+str((wallclock2-wallclock1)/concore.maxtime))

if GENERATE_PLOT == 0:
    quit()

# --- FINAL SAVE & CLEANUP ---
plt.ioff()
fig_ym.savefig("hrmap.pdf")
fig_u.savefig("stim.pdf")
plt.show()


