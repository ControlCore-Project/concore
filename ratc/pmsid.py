import concore
import numpy as np
from scipy.interpolate import interp1d 
from scipy.integrate import solve_ivp

import matplotlib.pyplot as plt
import numpy.matlib


class constant:
    
    #Constant of CVS model
    CVS_R1 = 0.01                  # Systemic resistance
    CVS_R2 = 0.0001                # Mitral Valve Resistance
    CVS_R3 = 0.008                 # Aortic Valve Resistance
    CVS_C2 = 20                    # Veneous compliance
    CVS_C3 = 1.8                   # Systemic compliance
    CVS_E_min = 0.02               # End-diastolic Elastance
    CVS_E_max = 1.2                # End-systolic Elastance
    CVS_L = 1e-6                   # Inertance 
    CVS_T0 = 60/450                # Baseline HR

    # Constant of baroreceptor 
    # Parameters for arterial wall deformation
    BR_Am = 15.71                  # Unstressed aortic cross-sectional area
    BR_A0 = 3.14                   # Maximum aortic cross-sectional area
    BR_a = 150                     # Saturation pressure
    BR_k = 5                       # Steepness constant
    # Parameters for mechanoreceptor model
    BR_a1 = 0.4                    # Nerve ending const
    BR_a2 = 0.5                    
    BR_b1 = 0.5                    # Nerve ending relaxation rate
    BR_b2 = 2
    # Parameters for BR firing model
    BR_s1 = 2.947e-10              # Firing constant
    BR_s2 = 3.473e-12
    BR_Cm = 37.5e-11               # Membrane capacitance 
    BR_gl = 5.019e-8               # Membrane conductance
    BR_Vth = 0.00116               # Voltage threshold
    BR_Tr = 0.0062                 # refractory period

    # Parameters of CNS 
    CNS_fes_inf = 3                # Sympathetic rate with maximum afferent inputs
    CNS_fes0 = 16                  # Sympathetic rate with minimum afferent inputs
    CNS_kes = 0.07                 # Steepness constant for sympathetic pathway
    CNS_fev_inf = 6                # Sympathetic rate with maximum afferent inputs
    CNS_fev0 = 3                   # Sympathetic rate with minimum afferent inputs
    CNS_kev = 7                    # Steepness constant for sympathetic pathway
    CNS_fas0 = 30                  # Central Frequency of Afferent Baroreceptor

    # Parameters of efferent pathways
    efrt_tau_E = 8/5               # Time Constant for Elastance Change
    efrt_tau_R = 6/5               # Time Constant for Systemic Resistance Change
    efrt_tau_Ts = 2/5              # Time Constant for Heart Period Change due to Sympathetic Stimulation
    efrt_tau_Tv = 1.5/5            # Time Constant for Heart Period Change due to Vagal Stimulation
    efrt_G_E = 0.3                 # Gain of Systolic Left Ventricular Elastance Change 
    efrt_G_R = 0.06                # Gain of Systemic Resistance  Change
    efrt_G_Ts = -0.01              # Gain of Heart Period Change by Sympathetic Stimulation
    efrt_G_Tv = 0.015              # Gain of Heart Period Chance by Vagal Stimulation
    efrt_fes_min = 3               # Minimum Sympathetic Frequency
    efrt_d_Ts = 0.4                # Delay in response of cardiac period through sympathetic pathway
    efrt_d_Tv = 0.04               # Delay in response of cardiac period through vagal pathway
    efrt_d_R = 0.4                 # Delay in response of systemic resistance
    efrt_d_E = 0.4                 # Delay in response of systolic elastance
    

    # Constant of Device Model
    stm_Gas = 178                  # Sensitivity of baroreceptive fibers               
    stm_Ges = 30                   # Sensitivity of sympathetic fibers   
    stm_Gev = 30                   # Sensitivity of vagal fibers
    stm_kw = 2.5e-4                # Scaling coefficient of pulse width
    stm_kf = 25                    # Scaling coefficient of pulse frequency
    stm_loc = np.eye(3)            # Fiber concentration in three stimulation locations



class cardiac(constant):
    
    
    def E(self, E_max, phi, Ts, Tv):
        tc = Ts + Tv - self.CVS_T0
        tn = phi*tc/(0.25/5 + tc*0.15)
        En = 1.55*(tn/0.5)**1.9/(1 + (tn/0.5)**1.9)/(1 + (tn/1.17)**21.9)
        return (E_max - self.CVS_E_min)*En + self.CVS_E_min 
    
    def ddefcn(self, t, y, Z, u, p):
        
        # y: state variable
        #   y(0) ~ left ventricular stressed volume
        #   y(1) ~ Left Atrial Pressure 
        #   y(2) ~ Arterial Pressure 
        #   y(3) ~ Aortic Flow 
        #   y(4) ~ Strain of Nerve Ending (first Voight Body)
        #   y(5) ~ Strain of Nerve Ending (Second Voight Body)
        #   y(6) ~ Heart Period due to Sympathetic Stimulation 
        #   y(7) ~ Heart Period due to Vagal Stimulation 
        #   y(8) ~ Systemic Resistance 
        #   y(9) ~ Maximum Left Ventricular Elastance 
        #   y(10) ~ frequency modulation variable
        
        dydt = np.zeros(11)
        self.x_inter.append(y[4])
        self.time.append(t)
        
        if len(self.x_inter) < 2:
            delay_func = interp1d(np.repeat(self.time, 2), np.repeat(self.x_inter, 2), kind="linear", bounds_error=False, 
                                  fill_value=(self.x_inter[0], self.x_inter[-1]))
        else:
            delay_func = interp1d(self.time, self.x_inter, kind="slinear", bounds_error=False,
                                  fill_value=(self.x_inter[0], self.x_inter[-1]))
        
        #Aterial wall deformation as function of blood pressure
        def AWD(P):
            A = (self.BR_Am - self.BR_A0)*P**self.BR_k/(self.BR_a**self.BR_k + P**self.BR_k) + self.BR_A0
            ew = 1 - np.sqrt(self.BR_A0)/np.sqrt(A)
            return ew
    
        # CNS relating afferent firing rate to sympathetic and vagal activity
        def fe(f_as, u, p):
            # Input : f_as ~ baseline afferent firing rate
            #         
            # Output : f = [fas, fes, fev]
            #          fas ~ baroreceptive firing rate with VNS
            #          fes ~ sympathetic firing rate with VNS
            #          fev ~ vagal firing rate with VNS
            
            uc1 = u[0]/self.stm_kw/np.sqrt(1 + (u[0]/self.stm_kw)**2)*u[1]/self.stm_kf/np.sqrt(1 + (u[1]/self.stm_kf)**2)
            uc2 = u[2]/self.stm_kw/np.sqrt(1 + (u[2]/self.stm_kw)**2)*u[3]/self.stm_kf/np.sqrt(1 + (u[3]/self.stm_kf)**2)
            uc3 = u[4]/self.stm_kw/np.sqrt(1 + (u[4]/self.stm_kw)**2)*u[5]/self.stm_kf/np.sqrt(1 + (u[5]/self.stm_kf)**2)
            
            uas = 1/3*self.stm_Gas*(self.stm_loc[0, 0]*p[0]*uc1 + self.stm_loc[0, 1]*p[1]*uc2 + self.stm_loc[0, 2]*p[2]*uc3)
            ues = 1/3*self.stm_Ges*(self.stm_loc[1, 0]*p[0]*uc1 + self.stm_loc[1, 1]*p[1]*uc2 + self.stm_loc[1, 2]*p[2]*uc3)
            uev = 1/3*self.stm_Gev*(self.stm_loc[2, 0]*p[0]*uc1 + self.stm_loc[2, 1]*p[1]*uc2 + self.stm_loc[2, 2]*p[2]*uc3)
            
            fas = f_as + uas
            fes = self.CNS_fes_inf + (self.CNS_fes0 - self.CNS_fes_inf)*np.exp(-self.CNS_kes*fas) + ues
            fev = (self.CNS_fev0 + self.CNS_fev_inf*np.exp((fas - self.CNS_fas0)/self.CNS_kev))/(1 + np.exp((fas - self.CNS_fas0)/self.CNS_kev)) + uev 
            f = [fas, fes, fev]
            return f
        
        # Cardiovascular model
        # isovolumetric relaxation and contraction phase
        if (y[2] - self.E(y[9], y[10], y[6], y[7])*y[0] >= 0 and self.E(y[9], y[10], y[6], y[7])*y[0] - y[1] >= 0):
            dydt[0] = 0
            dydt[1] = (y[2] - y[1])/self.CVS_C2/y[8]
            dydt[2] = (y[1] - y[2])/self.CVS_C3/y[8]
            dydt[3] = 0
        # ejection phase
        elif (y[2] - self.E(y[9], y[10], y[6], y[7])*y[0] < 0):
            dydt[0] = -y[3]
            dydt[1] = (y[2] - y[1])/self.CVS_C2/y[8]
            dydt[2] = (y[1] - y[2])/self.CVS_C3/y[8] + y[3]/self.CVS_C3
            dydt[3] = 1/self.CVS_L*(self.E(y[9], y[10], y[6], y[7])*y[0] - self.CVS_R3*y[3] - y[2])
        # filling phase
        elif (self.E(y[9], y[10], y[6], y[7])*y[0] - y[1] < 0):
            dydt[0] = (y[1] - self.E(y[9], y[10], y[6], y[7])*y[0])/self.CVS_R2
            dydt[1] = (y[2] - y[1])/self.CVS_C2/y[8] + (self.E(y[9], y[10], y[6], y[7])*y[0] - y[1])/self.CVS_C2/self.CVS_R2
            dydt[2] = (y[1] - y[2])/self.CVS_C3/y[8]
            dydt[3] = 0
        
        # Integrate-and-fire baroreceptive firing rate
        ew = AWD(y[2])    
        dydt[4] = -(self.BR_a1 + self.BR_a2 + self.BR_b1)*y[4] + (self.BR_b1 - self.BR_b2)*y[5] + (self.BR_a1 + self.BR_a2)*ew
        dydt[5] = - self.BR_a2*y[4] - self.BR_b2*y[5] + self.BR_a2*ew
        Ine1 = self.BR_s1*(ew - delay_func(t-Z[0])) + self.BR_s2
        Ine2 = self.BR_s1*(ew - delay_func(t-Z[1])) + self.BR_s2
        Ine3 = self.BR_s1*(ew - delay_func(t-Z[2])) + self.BR_s2
        Ine4 = self.BR_s1*(ew - delay_func(t-Z[3])) + self.BR_s2
        Ine = np.array([Ine1, Ine2, Ine3, Ine4])
        f_as = np.zeros([4, 1])
        f = np.zeros([4, 3])
        for i in range(0,4):     
            if (Ine[i] - self.BR_gl*self.BR_Vth > 0):
                T = self.BR_Cm/self.BR_gl*np.log(Ine[i]/(Ine[i] - self.BR_gl*self.BR_Vth))
                f_as[i, :] = 1/(T + self.BR_Tr)
            else:
                f_as[i, :] = 0
            
            f[i, :] = fe(f_as[i, :], u, p)
        
        # Effector's response
        dydt[6] = -(y[6] - self.CVS_T0)/self.efrt_tau_Ts + self.efrt_G_Ts*np.log(np.max([f[0, 1] - self.efrt_fes_min, 0]) + 1)
        dydt[7] = -(y[7] - self.CVS_T0)/self.efrt_tau_Tv + self.efrt_G_Tv*f[1, 2]
        dydt[8] = -(y[8] - self.CVS_R1)/self.efrt_tau_R + self.efrt_G_R*np.log(np.max([f[2,1] - self.efrt_fes_min, 0]) + 1)
        dydt[9] = -(y[9] - self.CVS_E_max)/self.efrt_tau_E + self.efrt_G_E*np.log(np.max([f[3, 1] - self.efrt_fes_min, 0]) + 1)
        dydt[10] = 1/(y[6] + y[7] - self.CVS_T0)
            
        return dydt

    def Cardiac_model(self, uc, pl, N, ini):
        # input : uc ~ pulse width and pulse frequency of three stimulation locations
        #         pl ~ activation condition of three stimulation locations
        #         N ~ number of cardiac cycles
        #         ini ~ initial condition 
        #         par ~ model parameters
        
        # output: t_tot ~ continuous time
        #         x_tot ~ state variables
        #         E_lv ~ elastance of left ventricle
        #         HR_tot ~ mean heart rate
        #         MAP_tot ~ mean arterial pressure
       
        # Set integral conditions            
        dt = 1e-4
        t_span = np.arange(0, 5, dt)
        delay = [self.efrt_d_Ts, self.efrt_d_Tv, self.efrt_d_R, self.efrt_d_E] 
        # Set initial input
        p = pl[:, 0]
        # Record state variables and outputs
        t_tot = [0]         # Time
        x_tot = np.asarray(ini).reshape(1, -1)         # State variables
        MAP_tot = []       # Mean arterial pressure
        MHR_tot = []       # Mean heart rate
        E_lv = []          # Elastance of left ventricle
        
        # Define events
        def event(t, y, Z, u, p):
            return 1 - y[-1]
        event.terminal = True
        event.direction = -1
            
        for kk in range(0, N):
            #Store Values
            u = uc[kk] 
            self.x_inter = []
            self.time = []
            sol = solve_ivp(self.ddefcn, [t_span[0], t_span[-1]], x_tot[-1], method = "RK23", t_eval=t_span, events=event, 
                            #max_step = 5*dt, 
                            args = (delay, u, p))

            if sol.success:
                MHR_tot += [60/np.mean(sol.y.T[:, 6] + sol.y.T[:, 7] - self.CVS_T0)]
                MAP_tot += [np.mean(sol.y.T[:,2])]
                
                # Define new loop inputs
                x_tot = np.row_stack((x_tot[:-1], sol.y.T, sol.y_events[-1]))
                t_tot = np.append(np.append(t_tot[:-1], sol.t), sol.t_events[-1]).reshape(-1,)
                t_span = np.arange(sol.t_events[-1], sol.t_events[-1] + 5, dt)
                x_tot[-1, -1] = 0
            else:
                print(f"solve_ivp failed with error {sol.message}")
                break
            
        E_lv = self.E(x_tot[:, 9], x_tot[:, 10], x_tot[:, 6], x_tot[:, 7])       
        return t_tot, x_tot, E_lv, MHR_tot, MAP_tot
    
    def model_plot(self, t_tot, x_tot, E_lv, MHR_tot, MAP_tot, Nsim, uc):
        # Input variables
        fig, ax = plt.subplots(3,2, figsize=(10,10))
        ax[0,0].plot(uc[:,0])
        ax[0,0].set(xlabel="Cardiac Cycle", ylabel="P_w (s)")
        
        ax[0,1].plot(uc[:,1])
        ax[0,1].set(xlabel="Cardiac Cycle", ylabel="P_f (Hz)")
        
        ax[1,0].plot(uc[:,2])
        ax[1,0].set(xlabel="Cardiac Cycle", ylabel="P_w (s)")
        
        ax[1,1].plot(uc[:,3])
        ax[1,1].set(xlabel="Cardiac Cycle", ylabel="P_f (Hz)")
        
        ax[2,0].plot(uc[:,4])
        ax[2,0].set(xlabel="Cardiac Cycle", ylabel="P_w (s)")
    
        ax[2,1].plot(uc[:,5])
        ax[2,1].set(xlabel="Cardiac Cycle", ylabel="P_f (Hz)") 
        plt.show()
        
        # Time course of MAP and HR
        fig, ax = plt.subplots(2,1, figsize=(10, 10))
        ax[0].plot(MAP_tot, 'o')
        ax[0].set(xlabel="Cardiac Cycle", ylabel="MAP (mmHg)")
        ax[1].plot(MHR_tot, 'o')
        ax[1].set(xlabel="Cardiac cycle", ylabel="HR (bpm)")
        plt.show()
        
        # Time course of left ventricular Elastance
        fig, ax = plt.subplots(1,2, figsize=(10,10))
        ax[0].plot(t_tot, E_lv)
        ax[0].set(xlabel="t (s)", ylabel="E_{LV} (mmHg/mm^3)")
        # Pressure-volume relationship of LV
        ax[1].plot(x_tot[:, 0] + 50, E_lv*x_tot[:, 0])
        ax[1].set(xlabel="Volume (mm^3)", ylabel="Pressure (mmHg)")
        plt.show()
        
        # Time course of LV, Vein and arterial pressure
        plt.plot(t_tot, E_lv*x_tot[:, 0])
        plt.plot(t_tot, x_tot[:, 1])
        plt.plot(t_tot, x_tot[:, 2])
        plt.legend(['LV','Vein','Artery'])
        plt.xlabel('t (s)')
        plt.ylabel('Pressure (mmHg)')
        plt.show()
        
        # Time course of systemic resistance
        fig, ax = plt.subplots(1,2, figsize=(10,10))
        ax[0].plot(t_tot, x_tot[:, 8])
        ax[0].set(xlabel="t (s)", ylabel="R_{sys} (mmHg*s/mm^3)")
        # Time course of maximum elastance of LV
        ax[1].plot(t_tot, x_tot[:, 9])
        ax[1].set(xlabel="t (s)", ylabel="E_{max} (mmHg/mm^3)")
        plt.show()
        
    def save_data(self, data):
        np.savetxt("{}.dat".format(data), data)



# initialize controller constant and variables
cm = cardiac()
concore.default_maxtime(150)

xm = np.array([217.77, 4.42, 108.84, 92.08, 0.17, 0.04, 0.13, 0.15, 0.12, 1.94, 0])
Nd = 3   # number of integer inputs
pl = np.ones([Nd, 1])          # Discrete inputs

concore.delay = 0.02
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

ym = np.array([concore.initval(init_simtime_ym)]).T
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        u = concore.read(1,"u",init_simtime_u)
    u = np.array(u).reshape(1, -1) #needs to be numpy col vect
    ###### Solve odes
    t_tot, x_tot, E_lv, MHR, MAP  = cm.Cardiac_model(u, pl, 1, xm)
    xm = np.array(x_tot[-1])
    ym = [MAP[0],MHR[0]]  #already a python list
    #####
    print("ym="+str(ym)+" u="+str(u));
    concore.write(1,"ym",ym,delta=1)
print("retry="+str(concore.retrycount))


