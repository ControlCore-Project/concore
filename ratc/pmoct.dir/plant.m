%--------------------------------------------------------------------------
% Model of Cardiovascular System by VNS
% 
% Yuyu Yao
% Oct 19, 2020
%--------------------------------------------------------------------------

function [ini, HR_tot, MAP_tot] = plant(uc, pl, N, ini, par)
% input : uc ~ pulse width and pulse frequency of three stimulation locations
%         pl ~ activation condition of three stimulation locations
%         N ~ number of cardiac cycles
%         ini ~ initial condition 
%         par ~ model parameters
%
% output: t_tot ~ continuous time
%         x_tot ~ state variables
%         E_lv ~ elastance of left ventricle
%         HR_tot ~ mean heart rate
%         MAP_tot ~ mean arterial pressure
   
% Set terminal options
option = odeset('event', @(t, y, Z)Event(t, y, Z, par));
% Set integral conditions
t_start = 0;        
t_end = 300;      
Ts = 1e-4;
tspan = t_start:Ts:t_end;
delay = [par.efrt.d_Ts, par.efrt.d_Tv, par.efrt.d_R, par.efrt.d_E];
% Set indices
kk = 0;             % Number of cardiac cycle
jj = 1;             % Number of integral solver 
% Set initial input
u = uc(:, 1);     
p = pl(:, 1);
% Record state variables and outputs
t_tot = [];         % Time
x_tot = [];         % State variables
MAP_tot = [];       % Mean arterial pressure
MHR_tot = [];       % Mean heart rate
E_lv = [];          % Elastance of left ventricle

while kk < N
    % Solve delayed ODE
    sol = dde23(@(t, y, Z)ddefcn(t, y, Z, u, p, par), delay, ini, tspan, option);
    % Update cardiac cycle number
    kk = kk + 1;    
    % Integral results 
    t = sol.x;   
    x = sol.y;
    te = sol.xe;
    xe = sol.ye;
    % Update initial condition and time span
    ini = xe;
    ini(end) = 0;
    t_start = te;
    tspan = t_start:Ts:t_end;
    % Update integer and continuous input
    u = uc(:, kk); 
    p = pl(:, kk);
    % Record process variables
    l = length(t);          
    ii = jj;
    jj = jj + l - 1;
    t_tot(ii:jj)= t;
    x_tot(:, ii:jj) = x;   
    % Calculate hemodynamic variables
    HR_tot(kk) = 60/mean(x(7, :) + x(8, :) - par.CVS.T0);
    MAP_tot(kk) = mean(x(3, :));     
end
 E_lv = E(x_tot(10, :), x_tot(11, :), x_tot(7, :), x_tot(8, :), par);
end

% Function of LV elastance
function y = E(E_max, phi, Ts, Tv, par)
tc = Ts + Tv - par.CVS.T0;
tn = phi.*tc./(0.25/5 + tc*0.15);
En = 1.55*(tn/0.5).^1.9./(1 + (tn/0.5).^1.9)./(1 + (tn/1.17).^21.9);
y = (E_max - par.CVS.E_min).*En + par.CVS.E_min;
end

% Aterial wall deformation as function of blood pressure
function ew = AWD(P, par)
A = (par.BR.Am - par.BR.A0).*P.^par.BR.k./(par.BR.a.^par.BR.k + P.^par.BR.k) + par.BR.A0;
ew = (sqrt(A) - sqrt(par.BR.A0))./sqrt(A);
end

% CNS relating afferent firing rate to sympathetic and vagal activity
function f = fe(f_as, u, p, par)
% Input : f_as ~ baseline afferent firing rate
%         
% Output : f = [fas, fes, fev]
%          fas ~ baroreceptive firing rate with VNS
%          fes ~ sympathetic firing rate with VNS
%          fev ~ vagal firing rate with VNS

f = [];
uc1 = u(1)/par.stm.kw/sqrt(1 + (u(1)/par.stm.kw)^2)*u(2)/par.stm.kf/sqrt(1 + (u(2)/par.stm.kf)^2);
uc2 = u(3)/par.stm.kw/sqrt(1 + (u(3)/par.stm.kw)^2)*u(4)/par.stm.kf/sqrt(1 + (u(4)/par.stm.kf)^2);
uc3 = u(5)/par.stm.kw/sqrt(1 + (u(5)/par.stm.kw)^2)*u(6)/par.stm.kf/sqrt(1 + (u(6)/par.stm.kf)^2);
uas = 1/3*par.stm.Gas*(par.stm.loc(1, 1)*p(1)*uc1 + par.stm.loc(1, 2)*p(2)*uc2 + par.stm.loc(1, 3)*p(3)*uc3);
ues = 1/3*par.stm.Ges*(par.stm.loc(2, 1)*p(1)*uc1 + par.stm.loc(2, 2)*p(2)*uc2 + par.stm.loc(2, 3)*p(3)*uc3);
uev = 1/3*par.stm.Gev*(par.stm.loc(3, 1)*p(1)*uc1 + par.stm.loc(3, 2)*p(2)*uc2 + par.stm.loc(3, 3)*p(3)*uc3);

fas = f_as + uas;
fes = par.CNS.fes_inf + (par.CNS.fes0 - par.CNS.fes_inf)*exp(-par.CNS.kes*fas) + ues;
fev = (par.CNS.fev0 + par.CNS.fev_inf*exp((fas - par.CNS.fas0)/par.CNS.kev))./(1 + exp((fas - par.CNS.fas0)/par.CNS.kev)) + uev; 

f(:, 1) = fas;
f(:, 2) = fes;
f(:, 3) = fev;
end

% Define events of each cardiac cycle
function [value, isterminal, direction] = Event(t, y, Z, par)
dP = 1 - y(11);
value = dP;
isterminal = 1;
direction = -1;
end

% Plant model
function dydt = ddefcn(t, y, Z, u, p, par)
% y: state variable
%   y(1) ~ left ventricular stessed volume
%   y(2) ~ Left Atrial Pressure 
%   y(3) ~ Arterial Pressure 
%   y(4) ~ Aortic Flow 
%   y(5) ~ Strain of Nerve Ending (first Voight Body)
%   y(6) ~ Strain of Nerve Ending (Second Voight Body)
%   y(7) ~ Heart Period due to Sympathetic Stimulation 
%   y(8) ~ Heart Period due to Vagal Stimulation 
%   y(9) ~ Systemic Resistance 
%   y(10) ~ Maximum Left Ventricular Elastance 
%   y(11) ~ frequency modulation variable

dydt = zeros(11, 1);
% Set delays   
ylag1 = Z(:, 1);
ylag2 = Z(:, 2);
ylag3 = Z(:, 3);
ylag4 = Z(:, 4); 
% Cardiovascular model
% isovolumetric relaxation and contraction phase
if y(3) - E(y(10), y(11), y(7), y(8), par)*y(1) >= 0 && E(y(10), y(11), y(7), y(8), par)*y(1) - y(2) >= 0
    dydt(1) = 0;
    dydt(2) = (y(3) - y(2))/par.CVS.C2/y(9);
    dydt(3) = (y(2) - y(3))/par.CVS.C3/y(9);
    dydt(4) = 0;
% ejection phase
elseif y(3) - E(y(10), y(11), y(7), y(8), par)*y(1) < 0
    dydt(1) = -y(4);
    dydt(2) = (y(3) - y(2))/par.CVS.C2/y(9);
    dydt(3) = (y(2) - y(3))/par.CVS.C3/y(9) + y(4)/par.CVS.C3;
    dydt(4) = 1/par.CVS.L*(E(y(10), y(11), y(7), y(8), par)*y(1) - par.CVS.R3*y(4) - y(3));
% filling phase
elseif E(y(10), y(11), y(7), y(8), par)*y(1) - y(2) < 0
    dydt(1) = (y(2) - E(y(10), y(11), y(7), y(8), par)*y(1))/par.CVS.R2 ;
    dydt(2) = (y(3) - y(2))/par.CVS.C2/y(9) + (E(y(10), y(11), y(7), y(8), par)*y(1) - y(2))/par.CVS.C2/par.CVS.R2;
    dydt(3) = (y(2) - y(3))/par.CVS.C3/y(9);
    dydt(4) = 0;
end 
% Integrate-and-fire baroreceptive firing rate
ew = AWD(y(3), par);    
dydt(5) = -(par.BR.a1 + par.BR.a2 + par.BR.b1)*y(5) + (par.BR.b1 - par.BR.b2)*y(6) + (par.BR.a1 + par.BR.a2)*ew;
dydt(6) = - par.BR.a2*y(5) - par.BR.b2*y(6) + par.BR.a2*ew;
Ine1 = par.BR.s1*(ew - ylag1(5)) + par.BR.s2;
Ine2 = par.BR.s1*(ew - ylag2(5)) + par.BR.s2;
Ine3 = par.BR.s1*(ew - ylag3(5)) + par.BR.s2;
Ine4 = par.BR.s1*(ew - ylag4(5)) + par.BR.s2;
Ine = [Ine1; Ine2; Ine3; Ine4];
f_as = zeros(4, 1);
f = zeros(4, 3);
for i = 1:4     
    if Ine(i) - par.BR.gl*par.BR.Vth > 0
        T = par.BR.Cm/par.BR.gl*log(Ine(i)./(Ine(i) - par.BR.gl*par.BR.Vth));
        f_as(i) = 1./(T + par.BR.Tr);
    else
        f_as(i) = 0;
    end
    f(i, :) = fe(f_as(i), u, p, par);
end
% Effector's response
dydt(7) = -(y(7) - par.CVS.T0)/par.efrt.tau_Ts + par.efrt.G_Ts*log(max([f(1, 2) - par.efrt.fes_min, 0])+1);
dydt(8) = -(y(8) - par.CVS.T0)/par.efrt.tau_Tv + par.efrt.G_Tv*f(2, 3);
dydt(9) = -(y(9) - par.CVS.R1)/par.efrt.tau_R + par.efrt.G_R*log(max([f(3,2) - par.efrt.fes_min, 0])+1);
dydt(10) = -(y(10) - par.CVS.E_max)/par.efrt.tau_E + par.efrt.G_E*log(max([f(4, 2) - par.efrt.fes_min, 0])+1);
dydt(11) = 1/(y(7) + y(8) - par.CVS.T0);
end