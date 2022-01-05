function [ini, y] = plant(uc, pl, N, ini, par)
% inputs : uc ~ pulse amplitude and frequency in three stimulation locations
%         pl ~ activation condition of three stimulation locations
%         N ~ number of cardiac cycles
%         ini ~ initial conditions 
%         par ~ model parameters
%
% outputs: can be found in the following parameter definition

t_start = 0;        
t_end = 300;      
Ts = 1e-3;
tspan = t_start:t_end;
delay = [par.efrt.d_Ts, par.efrt.d_Tv, par.efrt.d_Rsu, par.efrt.d_Rsl1, par.efrt.d_E, par.efrt.d_Vtot];
% Set terminal options
option = ddeset('event', @(t, y, Z)Event(t, y, Z, par), 'MaxStep', Ts);
kk = 0;                % index of cardiac cycle
jj = 1;                % index of integration step
% Record state variables and outputs
t_tot = [];            % Continous-time instance
x_tot = [];            % Continous-time state variables
ut = [];               % Continous-time stimulation parameters
pt = [];               % Continous-time stimulation locations        
MHRt = [];             % Continous-time heart rate
MAPt = [];             % Continous-time mean arterial pressure
td = [];               % time instance for each cardiac cycle
y = [];                % discrete heart rate for each cardiac cycle

while kk < N
    % Solve delayed ODE
    sol = dde23(@(t, y, Z)ddefcn(t, y, Z, uc(:, kk+1), pl(:, kk+1), par), delay, ini, tspan, option);
    % Update cardiac cycle number
    kk = kk + 1;
%     X = sprintf('Cardiac Cycle: %d', kk);
%     disp(X)
    % Integral results 
    t = sol.x;   
    x = sol.y;
    te = sol.xe;
    xe = sol.ye;
    % Update initial condition and time span
    ini = xe;
    ini(5) = 0;
    t_start = te;
    tspan = t_start:Ts:t_end;
    % Record process variables
    l = length(t);          
    ii = jj;
    jj = jj + l - 1;
    t_tot(ii:jj)= t;
    x_tot(:, ii:jj) = x; 
    MHR = 60/mean(x(8, :) + x(9, :) - par.efrt.T0);
    MAP = mean(x(1, :)); 
    y(:, kk) = [MAP; 60/MHR];
    ut(:, ii:jj) = repmat(uc(:, kk), 1, l);
    pt(:, ii:jj) = repmat(pl(:, kk), 1, l);
    MHRt(:, ii:jj) = repmat(MHR, 1, l);
    MAPt(:, ii:jj) = repmat(MAP, 1, l);
    td(kk) = ii;
end
end

% Define events of each cardiac cycle
function [value, isterminal, direction] = Event(t, y, Z, par)
dP = 1 - y(5);
value = dP;
isterminal = 1;
direction = -1;
end

% Function of LV pressure
function y = P_lh(x, par)
T = x(8) + x(9) - par.efrt.T0;
Tsys = par.CVS.Tsys0 - par.CVS.ksys/T;
if x(5) >= 0 && Tsys/T >= x(5)
    phi = sin(pi*T*x(5)/Tsys);
else
    phi = 0;
end
y = phi*x(12)*(x(4) - par.CVS.Vu_lh)...
    + (1 - phi)*par.CVS.P0_lh*(exp(par.CVS.kE_lh*x(4))-1);
end

% Aterial wall deformation as function of blood pressure
function ew = AWD(P, par)
A = (par.BR.Am - par.BR.A0).*P.^par.BR.k./(par.BR.a.^par.BR.k + P.^par.BR.k) + par.BR.A0;
ew = (sqrt(A) - sqrt(par.BR.A0))./sqrt(A);
end

% CNS relating afferent firing rate to sympathetic and vagal activity
function f = fe(SV1, Pau, u, p, par)
% Input : x ~ state variables
%         
% Output : f = [fas, fes, fev]
%          fes ~ sympathetic firing rate with VNS
%          fev ~ vagal firing rate with VNS
ew = AWD(Pau, par);  
Ine = par.BR.s1*(ew - SV1) + par.BR.s2;
if Ine - par.BR.gl*par.BR.Vth > 0
    T = par.BR.Cm/par.BR.gl*log(Ine./(Ine - par.BR.gl*par.BR.Vth));
    fasf = 1./(T + par.BR.Tr);
else
    fasf = par.BR.fas_min;
end
% modified baroreceptive firing rate
Pas1 = exp((u(1) - par.stm.Ias1)/par.stm.kas1)./(1 + exp((u(1) - par.stm.Ias1)/par.stm.kas1));
fas1 = (par.stm.Pas0 + par.stm.Pass*u(2) + par.stm.Pasp*fasf)*(u(2) + fasf);
Pas2 = exp((u(3) - par.stm.Ias2)/par.stm.kas2)./(1 + exp((u(3) - par.stm.Ias2)/par.stm.kas2));
fas2 = (par.stm.Pas0 + par.stm.Pass*u(4) + par.stm.Pasp*fasf)*(u(4) + fasf);
Pas3 = exp((u(5) - par.stm.Ias3)/par.stm.kas3)./(1 + exp((u(5) - par.stm.Ias3)/par.stm.kas3));
fas3 = (par.stm.Pas0 + par.stm.Pass*u(6) + par.stm.Pasp*fasf)*(u(6) + fasf);
fas = p(1)*par.stm.C(1, 1)*Pas1*fas1 + p(2)*par.stm.C(1, 2)*Pas2*fas2 + p(3)*par.stm.C(1, 3)*Pas3*fas3 + (1 - p(1)*par.stm.C(1, 1)*Pas1 - p(2)* par.stm.C(1, 2)*Pas2 - p(3)*par.stm.C(1, 3)*Pas3)*fasf;
% physiologically efferent firing rate
fesf = par.CNS.fes_inf + (par.CNS.fes0 - par.CNS.fes_inf)*exp(-par.CNS.kes*fas) + par.CNS.dfes;
fevf = (par.CNS.fev0 + par.CNS.fev_inf*exp((fas - par.CNS.fas0)/par.CNS.kev))./(1 + exp((fas - par.CNS.fas0)/par.CNS.kev)) + par.CNS.dfev;
% modified vagal firing rate 
Pev1 = exp((u(1) - par.stm.Iev1)/par.stm.kev1)./(1 + exp((u(1) - par.stm.Iev1)/par.stm.kev1));
fev1 = (par.stm.Pev0 + par.stm.Pevs*u(2) + par.stm.Pevp*fevf)*(u(2) + fevf);
Pev2 = exp((u(3) - par.stm.Iev2)/par.stm.kev2)./(1 + exp((u(3) - par.stm.Iev2)/par.stm.kev2));
fev2 = (par.stm.Pev0 + par.stm.Pevs*u(4) + par.stm.Pevp*fevf)*(u(4) + fevf);
Pev3 = exp((u(5) - par.stm.Iev3)/par.stm.kev3)./(1 + exp((u(5) - par.stm.Iev3)/par.stm.kev3));
fev3 = (par.stm.Pev0 + par.stm.Pevs*u(6) + par.stm.Pevp*fevf)*(u(6) + fevf);
fev = p(1)*par.stm.C(3, 1)*Pev1*fev1 + p(2)*par.stm.C(3, 2)*Pev2*fev2 + p(3)*par.stm.C(3, 3)*Pev3*fev3 + (1 - p(1)*par.stm.C(3, 1)*Pev1 - p(2)*par.stm.C(3, 2)*Pev2 - p(3)*par.stm.C(3, 3)*Pev3)*fevf;
% modified sympathetic firing rate
Pes1 = exp((u(1) - par.stm.Ies1)/par.stm.kes1)./(1 + exp((u(1) - par.stm.Ies1)/par.stm.kes1));
fes1 = (par.stm.Pes0 + par.stm.Pess*u(2) + par.stm.Pesp*fesf)*(u(2) + fesf);
Pes2 = exp((u(3) - par.stm.Ies2)/par.stm.kes2)./(1 + exp((u(3) - par.stm.Ies2)/par.stm.kes2));
fes2 = (par.stm.Pes0 + par.stm.Pess*u(4) + par.stm.Pesp*fesf)*(u(4) + fesf);
Pes3 = exp((u(5) - par.stm.Ies3)/par.stm.kes3)./(1 + exp((u(5) - par.stm.Ies3)/par.stm.kes3));
fes3 = (par.stm.Pes0 + par.stm.Pess*u(6) + par.stm.Pesp*fesf)*(u(6) + fesf);
fes = p(1)*par.stm.C(2, 1)*fes1*Pes1 + p(2)*par.stm.C(2, 2)*fes2*Pes2 + p(3)*par.stm.C(2, 3)*fes3*Pes3 + (1 - p(1)*par.stm.C(2, 1)*Pes1 - p(2)*par.stm.C(2, 2)*Pes2 - p(3)*par.stm.C(2, 3)*Pes3)*fesf;
f = [fas; fes; fev];
end

% Plant model
function dydt = ddefcn(t, y, Z, u, p, par, par_HF)
%   y: state variable
%   y(1) ~ upper body arterial pressure
%   y(2) ~ lower body venous pressure
%   y(3) ~ upper body venous pressure
%   y(4) ~ volume of left heart
%   y(5) ~ frequency modulation variable
%   y(6) ~ first voigt body strain
%   y(7) ~ second voigt body strain
%   y(8) ~ heart period due to sympathetic drive
%   y(9) ~ heart period due to vagal drive
%   y(10) ~ upper body resistance 
%   y(11) ~ lower body reistance
%   y(12) ~ left heart elastance
%   y(13) ~ total blood volume
dydt = zeros(13, 1);
% Set delays   
ylag1 = Z(:, 1);
ylag2 = Z(:, 2);
ylag3 = Z(:, 3);
ylag4 = Z(:, 4); 
ylag5 = Z(:, 5);
ylag6 = Z(:, 6);
% isovolumetric relaxation and contraction phase
if y(1) - P_lh(y, par) >= 0 && P_lh(y, par) - y(3) >= 0
    Sav = 0;
    Smv = 0;
% ejection phase
elseif y(1) - P_lh(y, par) < 0
    Sav = 1;
    Smv = 0;
% filling phase
elseif P_lh(y, par) - y(3) < 0
    Sav = 0;
    Smv = 1;
end   
Rsl = y(11)*par.CVS.Rsl2/(y(11) + par.CVS.Rsl2);
Pal = (y(13) - y(1)*par.CVS.Cau - y(2)*par.CVS.Cvl - y(3)*par.CVS.Cvu - y(4))/par.CVS.Cal;
dydt(1) = 1/par.CVS.Cau*(Sav*(P_lh(y, par) - y(1))/par.CVS.Rav - (y(1) - y(3))/y(10) -  (y(1) - Pal)/par.CVS.Rsa);
dydt(2) = 1/par.CVS.Cvl*((Pal - y(2))/Rsl - (y(2) - y(3))/par.CVS.Rsv);
dydt(3) = 1/par.CVS.Cvu*((y(2) - y(3))/par.CVS.Rsv + (y(1) - y(3))/y(10) - Smv*(y(3) - P_lh(y, par))/par.CVS.Rmv); 
dydt(4) = Smv*(y(3) - P_lh(y, par))/par.CVS.Rmv - Sav*(P_lh(y, par) - y(1))/par.CVS.Rav;
dydt(5) = 1/(y(8) + y(9) - par.efrt.T0);
% Integrate-and-fire baroreceptive firing rate
ew = AWD(y(1), par);
dydt(6) = -(par.BR.a1 + par.BR.a2 + par.BR.b1)*y(6) + (par.BR.b1 - par.BR.b2)*y(7) + (par.BR.a1 + par.BR.a2)*ew;
dydt(7) = - par.BR.a2*y(6) - par.BR.b2*y(7) + par.BR.a2*ew;
SVlag = [ylag1(6); ylag2(6); ylag3(6); ylag4(6); ylag5(6); ylag6(6)];
f = zeros(3, 6);
for i = 1:6
    f(:,i) = fe(SVlag(i), y(1), u, p, par);
end
% Effector's response
dydt(8) = (-(y(8) - par.efrt.T0) + par.efrt.G_Ts*log(max([f(2, 1) - par.efrt.fes_min, 0])+1))/par.efrt.tau_Ts;
dydt(9) = (-(y(9) - par.efrt.T0) + par.efrt.G_Tv*f(3, 2))/par.efrt.tau_Tv;
dydt(10) = (-(y(10) - par.efrt.Rsu0) + par.efrt.G_Rsu*log(max([f(2, 3) - par.efrt.fes_min, 0])+1))/par.efrt.tau_Rsu;
dydt(11) = (-(y(11) - par.efrt.Rsl10) + par.efrt.G_Rsl1*log(max([f(2, 4) - par.efrt.fes_min, 0])+1))/par.efrt.tau_Rsl1;
dydt(12) = (-(y(12) - par.efrt.Emax_lh0) + par.efrt.G_E*log(max([f(2, 5) - par.efrt.fes_min, 0])+1))/par.efrt.tau_E;
dydt(13) = (-(y(13) - par.efrt.Vtot0) + par.efrt.G_Vtot*log(max([f(2, 6) - par.efrt.fes_min, 0])+1))/par.efrt.tau_Vtot;
end