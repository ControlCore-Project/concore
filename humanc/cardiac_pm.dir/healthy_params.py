
"""
Created on Thu Sep 30 05:21:27 2021

@author: Sanmi
"""
import numpy as np




#cardiosystem

Csa = 0.28
Csp = 2.05
Cep = 1.36
Cmp = 0.31
Csv = 43.11
Cev = 28.4
Cmv = 6.6
Ctv = 33
Cpa = 0.67
Cpp = 5.80
Cpv = 25.37


 
Vusa = 0
Vusp = 274.4
Vuep = 274.1 
Vusv = 986.48
Vuev = 484
Vupa = 0
Vupp = 123
Vupv = 120
Vumv = 93.1
Vump = 62.5 
Vutv = 0


Rsa = 0.06
Rsp = 3.307
Rep = 1.725
Rmp = 4.13
Rsv = 0.038
Rev = 0.0197
Rmv = 0.0848
Rtv = 0.0054
Rpa = 0.023
Rpp = 0.0894
Rpv = 0.0056



Rd = 10000


P0 = 3.9

#left heart
Cla = 19.23
Vula = 25
Rla = 0.003
Polv = 1.5
Kelv = 0.014
Vulv = 16.77

KRlv = 0.0004

#right heart
Cra = 31.25
Vura = 25
Rra = 0.0025
Porv = 1.5
Kerv = 0.011
Vurv = 40.8
KRrv = 0.0014


ksys = 0.075
Tsys0 = 0.4
Vt = 5000


Lsa = 0.00022
Lpa = 0.00018
 
#baroreceptor
fbrmin = 2.52
tauz = 6.37
fbrmax = 47.78
taup = 2.067
Pn = 92
ka = 11.758

Tresp = 4

#cpr receptor
fmaxl = 20
Ptn = 10.8
kl = 11.758
taucp = 2

#lung stretch receptor
taulung = 2
Gal = 12
vlung0  = 0.583

#parasympathetic branch # br, cpr, lr

fmin = np.array([0.3, 0.451, 2.75])
midpt = np.array([44.3, 10.2, 10])
fmax = np.array([21.5, 28.357, 31.57 ])
k = np.array([2.14,1.636, 7.516])


kreceptor = np.array([[1,1,1],[0,1,1]])



#NA, DMV, NActr

foutmin = np.array([4.88, 2.59, 0.61])
foutmidpt = np.array([60, 43.1, 9.8])
foutmax = np.array([15.78,6.66, 11])
foutk = np.array([2.55, 1.24, 1.2])

#T, Emaxlv, Emaxrv effectors
tauv = np.array([1.5,2,2])
Gv = np.array([0.09, 0.205, 0.347])
dv = 0.2

#sympathetic branch
G = np.array([[1, 2, -1.1541],[1, 2.5, 0.33],[1,0,0]]) # br, cpr,lr, 

fesinf = 2.1
fes0 = 16.11
fesmin = 2.66
kes = 0.0675

theta0 = np.array([0.58, 1.283, 0.757, 2.49, 0.96, 4.13, 1435.4, 1247, 290])

Gs = np.array([-0.13, -0.13, -0.22, 0.695, 0.653, 2.81, -265.4, -107.5, -25])
taus = np.array([2,2,2,6,6,6,20,20,6])
ds = np.array([2,2,2])


Vu = np.array([Vusa,Vusp,theta0[6], theta0[7],theta0[8], Vutv, Vura, Vupa, Vupp,Vupv, Vula, Vulv, Vurv])
xstart = np.concatenate((np.zeros(15),np.array([-0.25, 1, -0.25, 1]),Vu))