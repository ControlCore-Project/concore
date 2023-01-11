"""
Created on Tue Oct  5 09:28:38 2021
@author: Sanmi

Provides the various sub-functions for the human cardiac model
"""

import numpy as np
import healthy_params as K



def phi_function(u,T):
    """
    Parameters
    ----------
    u : real value between [0,1]
        u marks the progress of a heart cycle.        
    T : real, positive
        Heart period

    Returns
    -------
    phi : real, [0,1]
        Describes the state of contraction/relaxation of the heart
    """
    Tsys = K.Tsys0 - K.ksys/T
    if u<=Tsys/T:
        d=  np.sin(np.pi* u *T/Tsys)
        phi = d**2
    else:
        phi = 0 
    
    return phi


def flow_function(x,y,R):
    """
    Describes valve action in the 4 chambers of the heart

    Parameters
    ----------
    x : real, non-negative
        pressure
    y : real, non-negative
        pressure
    R : real, non-negative
        resistance to flow

    Returns
    -------
    output : real, non-negative
             volumetric flow out of heart chamber    

    """
    if x <= y:
        output = 0
    else:
        output = (x-y)/R
    return output


def abd_pressure(u):
    """
    
    Parameters
    ----------
    u : real, [0,1]
        Marks the progress of a respiratory cycle

    Returns
    -------
    y : real, non-negative
    cyclic abdominal pressure

    """
    Tresp = 4
    Tinsp = 1.6
    Texp = 1.4
    
    if u < (Tinsp/2)/Tresp:
        y = -2.5*u*Tresp/(Tinsp/2)
        
    elif u < Tinsp/Tresp:
        y = -2.5
    elif  u < (Tinsp + Texp)/Tresp:
        y = -2.5*(Tinsp + Texp - u*Tresp)/Texp
    else:
        y = 0
    return y


def thoracic_pressure(u):
    """
    Parameters
    ----------
    u : real, [0,1]
        Marks the progress of a respiratory cycle

    Returns
    -------
    y : real, non-negative
        cyclic thoracic pressure
    """
    Pthor_max = -4
    Pthor_min = -9
    Tresp = 4
    Tinsp = 1.6
    Texp = 1.4
    
    if u < Tinsp/Tresp:
        y = Pthor_max - (Pthor_max - Pthor_min)*(Tresp/Tinsp)*u
    elif u < (Tinsp + Texp)/Tresp:
        y = Pthor_max - (Pthor_max - Pthor_min)/Texp*(Tinsp + Texp - u*Tresp)
    else:
        y = Pthor_max
    return y


def gen_sigmoid(x,xmid,ymin, ymax,k):
    """
    Implements a sigmoid function mapping

    Parameters
    ----------
    x : number to be converted
        pressure or firing rate
    xmid : 
        x-value that generates average output
    ymin : lower bound of output (real)
    ymax : upper bound of output (real)
        
    k : real, parameter that describes the steepness of the sigmoid curve
    

    Returns
    -------
    output : real number
        
    """
    dummy = np.exp((x-xmid)/k)
    top = ymin + ymax*dummy
    bottom = 1+ dummy
    output = top/bottom
    return output


def cpr(Pl):
    """
    Converts pressure recorded by cardiopulmonary receptors to a firing rate
    via a sigmoid function

    Parameters
    ----------
    Pl : Pressure (mmHg)
    
    Returns
    -------
    output : firing rate (fcpr (Hz))
 

    """
    num = K.fmaxl
    den = 1 + np.exp((K.Ptn-Pl)/K.kl)
    return  num/den
    

def sympathetic_outflow(f):
    """
    

    Parameters
    ----------
    f : real
        sympathetic firing rate

    Returns
    -------
    f_effector : real
        effector firing rate 

    """
    f_effector = K.fesinf + (K.fes0 - K.fesinf)*np.exp(-1*K.kes * f)
    return f_effector


def calc_sigma(Gs,fhist,fesmin):
    """
    

    Parameters
    ----------
    Gs : real
        Effector gain
    fhist : delayed firing rate
   .
    fesmin : real
        min firing rate.

    Returns
    -------
    output : real
        Forcing function for effector ODE.

    """
    if fhist>fesmin:
        output = Gs*np.log(fhist-fesmin+1)
    else:
        output = 0
    return output




def generate_historylist(dt = 0.001, ds = K.ds, dv = K.dv):
    """
    
    Parameters
    ----------
    
    dt : sampling time
        
    ds : TYPE, optional
        time delay in sympathetic branch. 
    dv : time delay in parasympathtic branch

    Returns
    -------
    Five lists (histories) of firing rates in the sympathetic (3) and vagal (2)
    pathways
    """
    
    sym1 = [20]*int(ds[0]/dt)
    sym2 = [3]*int(ds[1]/dt)
    sym3 = [3]*int(ds[2]/dt)
    
    fpara1 = [10]*int(dv/dt)
    fpara2 = [10]*int(dv/dt)
    return np.array(sym1 + sym2 + sym3 + fpara1 +  fpara2)

def update_historylist(fsym1,fsym2,fsym3, fpara1, fpara2,hs1,hs2,hs3,hp1, hp2):
    """
    Updates lists(h) of past firing rates. Discards the earliest and appends the latest.

    Parameters
    ----------
    """
    hs1.append(fsym1)
    hs1.pop(0)
    
    hs2.append(fsym2)
    hs2.pop(0)
    
    hs3.append(fsym3)
    hs3.pop(0)
    
    hp1.append(fpara1)
    hp1.pop(0)
    
    hp2.append(fpara2)
    hp2.pop(0)
    
    return(hs1,hs2,hs3,hp1,hp2)

def split_states(x):
    """
    Splits states of the cardiac model into real states and firing histories    

    Parameters
    ----------
    
    """
    real_state = x[0:31]
    hs1 = list(x[31:2031])
    hs2 = list(x[2031:4031])
    hs3 = list(x[4031:6031])
    hp1 = list(x[6031:6231])
    hp2 = list(x[6231:6431])
    
    return real_state, hs1,hs2,hs3,hp1,hp2


def stimulation(fphys, amplitude, fstim,j):
    """
    Describes the effect of VNS stimulation (amplitude and frequency) on 
    physiological firing rate

    Parameters
    ----------
    fphys : physiological firing rate
        
    amplitude : VNS amplitude 
        
    fstim : VNS frequency
        
    j : 0 : afferent, 1: efferent

    Returns
    -------
    new_freq : effective firing rate after stimulation

    """
    #amplitude_effect
    xmid = np.array([0.3, 1.7])
    k = np.array([0.06, 0.35])
    ymin = 0
    ymax = 1
    R = gen_sigmoid(amplitude, xmid[j], ymin, ymax,k[j])
    
    #frequency effect
    alpha = 1 - (fphys+fstim)/60
    
    new_freq = (1-R)*fphys + R*alpha*(fphys + fstim)
    return new_freq




def hcm_pulsatile_dde(x,ustar, hs1,hs2,hs3, hp1,hp2):
    """
    
    Parameters
    ----------
    x : current states (31)
    ustar : 2 by 0 array (amplitude and frequency)
    hs1...hp2: delayed sympathetic and parasympathetic firing rates    
    
    Returns
    -------
    new firing rates (to be stored)
    derivatives of the ODEs
    """
   
    
        
    u,zeta,dTs, dTv,dEls, dElv, dErs, dErv, dRsp, dRep, dRmp, dVusv,dVuev,\
        dVumv,Ppa,Fpa,Ppp,Ppv,Psa,Fsa,Psp,Pev,Ptv,Pla,Pra,\
       Ptilde,Pl, flr, Vmv,Vlv, Vrv = x
       
    T = dTs + dTv + K.theta0[0]
    Emaxlv =  K.theta0[1] + 1/(dEls + dElv)
    Emaxrv =  K.theta0[2] + 1/(dErs + dErv)
    
    Rsp = dRsp + K.theta0[3]
    Rep = dRep + K.theta0[4]
    Rmp = dRmp + K.theta0[5]

    Vusv = dVusv + K.theta0[6]
    Vuev = dVuev + K.theta0[7]
    Vumv = dVumv + K.theta0[8]
    
    Rlb = 1/((1/Rmp) + (1/K.Rd))

    Pthor = thoracic_pressure(zeta)
    vlung = K.vlung0-0.1*Pthor
    Pabd = abd_pressure(zeta)
    Psp_trans = Psp
    phi = phi_function(u,T)
    
    
    #left heart
    Pmaxlv = phi*Emaxlv*(Vlv-K.Vulv) + (1-phi)*K.Polv*(np.exp(K.Kelv*Vlv)-1)
    Rlv = K.KRlv*Pmaxlv
    Qol = flow_function(Pmaxlv,Psa,Rlv)
    Plv = Pmaxlv - Rlv*Qol
    Qil = flow_function(Pla, Plv,K.Rla)

    #right heart
    Pmaxrv = phi*Emaxrv*(Vrv-K.Vurv) + (1-phi)*K.Porv*(np.exp(K.Kerv*Vrv)-1)
    Rrv = K.KRrv*Pmaxrv
    Qor = flow_function(Pmaxrv,Ppa,Rrv)
    Prv = Pmaxrv - Rrv*Qor
    Qir = flow_function(Pra,Prv,K.Rra)

    Vu = K.Vusa + K.Vusp + K.Vump + K.Vuep + Vusv + Vuev + Vumv + K.Vutv + \
    K.Vura + K.Vupa + K.Vupp + K.Vupv + K.Vula 
    if Vmv >= Vumv:
        
        Pmv = ( 1/K.Cmv)*(Vmv-Vumv)
    else:
        Pmv = K.P0 *(1- (Vmv/Vumv)**(-1.5))
        
    Psv = (1/K.Csv)*(K.Vt - K.Csa*Psa - (K.Csp + K.Cep + K.Cmp)*Psp -\
                     K.Cev*Pev - K.Cmv*Pmv - K.Ctv*Ptv -K.Cra*Pra -\
                     K.Cpa*Ppa - K.Cpp*Ppp -K.Cpv*Ppv - K.Cla*Pla - Vu-Vlv-Vrv)
    
    if Pmv-Ptv>0:
        Vom = (Pmv-Ptv)/K.Rmv
    else:
        Vom = 0

    sigmas = np.zeros(9)    
    for j in range(3):
        sigmas[j] = calc_sigma(K.Gs[j],hs1,K.fesmin)
    
    
    dTsdt =  (sigmas[0] - dTs)/K.taus[0]
    dElsdt = (sigmas[1] - dEls)/K.taus[1]
    dErsdt = (sigmas[2] - dErs)/K.taus[2]
    
    for j in range(3,6):
        sigmas[j] = calc_sigma(K.Gs[j],hs2,K.fesmin)
        
    dRspdt = (sigmas[3] - dRsp)/K.taus[3]
    dRepdt = (sigmas[4] - dRep)/K.taus[4]
    dRmpdt = (sigmas[5] - dRmp)/K.taus[5]
    
    for j in range(6,9):
        sigmas[j] = calc_sigma(K.Gs[j],hs3,K.fesmin)
    dVusvdt = (sigmas[6] - dVusv)/K.taus[6]
    dVuevdt = (sigmas[7] - dVuev)/K.taus[7]  
    dVumvdt = (sigmas[8] - dVumv)/K.taus[8]   
    
    dudt = 1/T
    dzetadt = 1/K.Tresp
    Ppadt = (1/K.Cpa)*(Qor - Fpa)
    Fpadt = (1/K.Lpa)*(Ppa-Ppp - K.Rpa*Fpa)
    Pppdt = (1/K.Cpp)*(Fpa - (Ppp - Ppv)/K.Rpp)
    Ppvdt = (1/K.Cpv)*((Ppp-Ppv)/K.Rpp -(Ppv - Pla)/K.Rpv)
    Psadt = (1/K.Csa)*(Qol - Fsa)
    Fsadt = (1/K.Lsa) * (Psa - Psp - K.Rsa*Fsa)
    Pspdt = 1/(K.Csp + K.Cep + K.Cmp)*(Fsa - (Psp_trans - (Psv-Pabd))/Rsp - (Psp_trans-Pev)/Rep - (Psp-Pmv)/Rlb)
    Pevdt = (1/K.Cev) * ((Psp_trans-Pev)/Rep - (Pev-Ptv)/K.Rev - dVuevdt)
    Vmvdt = (Psp_trans-Pmv)/Rlb - Vom
    Ptvdt = (1/K.Ctv)*(Vom + (Pev-Ptv)/K.Rev + (Psv-Pabd-Ptv)/K.Rsv - (Ptv-Pra)/K.Rtv)
    Pladt = (1/K.Cla)*((Ppv-Pla)/K.Rpv- Qil)
    Pradt = (1/K.Cra)* ((Ptv-Pra)/K.Rtv - Qir)
    Vlvdt = Qil-Qol
    Vrvdt = Qir-Qor
    Ptildedt = (1/K.taup)*(Psa + K.tauz*Psadt - Ptilde)
    Pldt = (1/K.taucp)*(-Pl + Ppv-Pthor)
    flrdt =(1/K.taulung)*(-flr + K.Gal*vlung)

    
    #Autonomic regulation
    
    #sympathetic branch
    fbr = gen_sigmoid(Ptilde, K.Pn, K.fbrmin, K.fbrmax,K.ka)
    
    #Afferent VNS 
    nfbr = stimulation(fbr , ustar[0],ustar[1],0)
    fcpr = cpr(Pl)
    
    afferent = np.array([nfbr,fcpr,flr])
    f = np.matmul(K.G,afferent)
    f[1] -=25
    f_effectors = sympathetic_outflow(f)
    
      
    #parasympathetic branch
    frv = np.zeros_like(afferent)
    
    for i in range(3):
        frv[i] = gen_sigmoid(afferent[i],K.midpt[i],K.fmin[i],K.fmax[i],K.k[i])

    finput = np.matmul(K.kreceptor,frv)
    foNa = gen_sigmoid(finput[0],K.foutmidpt[0],K.foutmin[0], K.foutmax[0],K.foutk[0])
    nfoNa= stimulation(foNa , ustar[0], ustar[1],1)
    
    fDMV = gen_sigmoid(finput[1],K.foutmidpt[1],K.foutmin[1], K.foutmax[1],K.foutk[1])
    fDMV_NActr = fDMV + gen_sigmoid(nfoNa,K.foutmidpt[2],K.foutmin[2], K.foutmax[2],K.foutk[2])

    
    sigmav = np.zeros(3)
    sigmav[0] = K.Gv[0] * hp1
    dTvdt =  (sigmav[0] - dTv)/K.tauv[0]
    
    sigmav[1] = K.Gv[1]*hp2
    dElvdt = (sigmav[1] - dElv)/K.tauv[1]
    
    
    sigmav[2] = K.Gv[2]*hp2
    dErvdt = (sigmav[2] - dErv)/K.tauv[2]

    return (f_effectors[0],f_effectors[1],f_effectors[2],nfoNa,fDMV_NActr,\
            np.array((dudt, dzetadt,dTsdt, dTvdt, dElsdt,dElvdt,dErsdt,dErvdt,\
                      dRspdt,dRepdt,dRmpdt,dVusvdt,dVuevdt,dVumvdt,Ppadt,Fpadt, \
                     Pppdt, Ppvdt, Psadt, Fsadt, Pspdt,Pevdt, Ptvdt, \
                         Pladt, Pradt, Ptildedt,Pldt, flrdt,Vmvdt,Vlvdt, Vrvdt)))
        
 
       
def solve_hcm_pulsatile_dde(x,ustar,dt,hs1,hs2,hs3, hp1,hp2):
    """
    Solves the ODE system with the Euler method

    Parameters
    ----------
    x : current state, array of size 31
    ustar : VNS stimulation (amplitude and frequency)
    dt : sampling time
    hs1..hp2 : real, Delayed effector firing rates (sympathetic(s) and vagal(p))
        
    

    Returns
    -------
    fsym1..fpara2 : New firing rates (to be stored)
    new system states

    """
    fsym1,fsym2,fsym3, fpara1,fpara2,k1 = hcm_pulsatile_dde(x,ustar,hs1,hs2,hs3, hp1,hp2)
       
    return (fsym1,fsym2,fsym3 ,fpara1,fpara2, x + dt*k1)


def solve_hcm_pulsatile_dde_rk4(x,ustar,dt,hs1,hs2,hs3, hp1,hp2):
    """
    Solves the system of ODEs with the RK4 method
    Returns new firing rates and new system state
    """
    
    fsym1,fsym2,fsym3, fpara1,fpara2,k1 = hcm_pulsatile_dde(x,ustar,hs1,hs2,hs3, hp1,hp2)
    a1,a2,a3,a4,a5,k2 = hcm_pulsatile_dde(x + 0.5*dt*k1,ustar,hs1,hs2,hs3, hp1,hp2)
    a1,a2,a3,a4,a5,k3 = hcm_pulsatile_dde(x + 0.5*dt*k2,ustar,hs1,hs2,hs3, hp1,hp2)
    a1,a2,a3,a4,a5,k4 = hcm_pulsatile_dde(x + dt*k3,ustar,hs1,hs2,hs3, hp1,hp2)
    return (fsym1,fsym2,fsym3 ,fpara1,fpara2, x + (1/6)*dt*(k1+k2+2*k3 + k4))


def execute_pm(giantX, ustar):
    dt = 0.001
    max_time = 2 #arbitrarily large heart period (a cycle is unlikely to last 2 seconds)
    nx = 31  # number of system states
    x = np.inf * np.ones((nx,int((max_time/dt)+1)))
    x0, hs1,hs2,hs3,hp1,hp2 = split_states(giantX)
    x[:,0] = x0

    cycle_pressure = [] #holds arterial pressure values within a cycle
    
    k = 0
    flag = True
    while flag:
          
        fsym1,fsym2,fsym3, fpara1,fpara2, x[:,k+1] = solve_hcm_pulsatile_dde(x[:,k],ustar, dt, hs1[0],hs2[0],hs3[0],hp1[0],hp2[0])   
        cycle_pressure.append(x[18,k+1]) #store instantaneous arterial pressure
        
        if x[0,k+1]>=1: # check for end of cycle
            # ncycle +=1
            # print(ncycle)
           
            mapp = (max(cycle_pressure) + 2*min(cycle_pressure))/3 #MAP calculation
            
            hr = 60/ ((k+1)*dt) #hr calculation
            
            x[0,k+1] = 0 #reset cycle counter
            
            flag = False
            
        if x[1,k+1]>=1: #respiratory cycle refresh
            x[1,k+1] = 0
        
        hs1,hs2,hs3,hp1,hp2 =  update_historylist(fsym1,fsym2, fsym3,fpara1,fpara2,hs1,hs2, hs3,hp1,hp2)
        giantX = np.concatenate((x[:,k+1], np.array(hs1 + hs2 + hs3 + hp1 + hp2)))        
        k +=1
        
    
    return hr,mapp, giantX




    
   

def healthy_pm(giantX,ustar):
    """
    Determines hr and mean arterial pressure
    Parameters
    ----------
    giantX : array, current state of the system (including firing histories) 
    ustar : VNS stimulation, array (2 by 1), amplitude and frequency)
    
    Returns
    -------
    hr: Heart rate at the end of a cycle
    mapp: mean arterial pressure (mmHg) over the cycle
   
    """
    hr,mapp,giantX = execute_pm(giantX, ustar)
    return hr,mapp,giantX
    