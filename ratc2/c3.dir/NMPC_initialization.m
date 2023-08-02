function [regulator, sstarg, estmtr] = NMPC_initialization(disturbancemodel)
if ismac
    if length(version())>10
        addpath('casadi_mac', 'mpctools_mac')
    end
elseif isunix
    % Code to run on Linux platform
elseif ispc
    if length(version())>10
        addpath('casadi', 'mpctools')
    else
        addpath('casadi_octave', 'mpctools')
    end
else
    disp('Platform not supported')
end

load('nmpcData.mat', 'par')
mpc = import_mpctools();
% Parameters and sizes for the nonlinear system
Nx = par.nmpc.Nx;             % Number of states
Nu = par.nmpc.Nu;             % Number of inputs
Nu_est = par.nmpc.Nu_est;     % Number of inputs of estimator
Ny = par.nmpc.Ny;             % Number of outputs
Np = par.nmpc.Np;             % Number of parameters in regulator 
Nw = Nx;                      % Number of state noise
Nv = Ny;                      % Number of measurement noise
Nr = 10;                      % Prediction horizon
Ne = 10;                      % Estimator moving horizon
small = 1e-5;                 % small number
% Set initial guess for nonpulsatile model                                                                                            % Initial condition of nonpulsatile model
xs = par.nmpc.xs;             % guess of states                                            
us = par.nmpc.us;             % guess of inputs
ys = xs(1:2);                 % guess of outputs
p_gass = [1; 1; 1];           % guess of stimulation locations
% Define Casadi functions for regulator.
model_reg = @(x, u, p) ode_reg(x, u, p, par);
% Linearize the model at this point.
[A, B] = mpc.getLinearizedModel(model_reg, {xs, us, p_gass}, 'Delta', 0.14,'deal', true());
% Set weight matrix for cost function
dia = zeros(Nx, 1);
dia(1) = 1/xs(1)^2;
dia(2) = 100/xs(2)^2;
Qr = diag(dia);
Rr = 0.001*diag(1./us.^2);
[~, Pr] = dlqr(A, B, Qr, Rr);
% Set matrices for disturbance model
switch disturbancemodel
case 'Good'
    Nd = 8;
    Bd = eye(Nu, Nd);
    Cd = zeros(Ny, Nd);
    Cd(1, 7) = 1;
    Cd(2, 8) = 1;
    Qd = diag([small*us.^2; ys(1)^2; ys(2)^2]);
case 'No'
    Nd = 8;
    Bd = zeros(Nu, Nd);
    Cd = zeros(Ny, Nd);
    Qd = eye(Nd);
end

% Get Kalman Filter weight as a prior.
Qe = small*diag(xs.^2);
Re = small*diag([ys(1); 0.1*ys(2)].^2);
Aaug = [A, B*Bd ; zeros(Nd, Nx), eye(Nd)];
Baug = [B; zeros(Nd, Nu)];
Gaug = eye(Nx + Nd);
Caug = [eye(Ny, Nx), Cd];
Qaug = blkdiag(Qe, Qd);
Raug = Re;
detec = rank([eye(Nx + Nd) - Aaug; Caug]);
if detec < Nx + Nd
    Aaug = Aaug - 1e-6*eye(size(Aaug)); % Help out dlqe a bit.
end
[Lkf, ~, Pe] = dlqe(Aaug, Gaug, Caug, Qaug, Raug);
% Set casadi function
ode_reg_casadi = mpc.getCasadiFunc(@(x, u, Bd, d, p)model_reg(x, u + Bd*d, p),...
    {Nx, Nu, [Nu, Nd], Nd, Np}, {'x', 'u', 'Bd', 'd', 'p'}, {'ode_reg_casadi'}, ...
    'rk4', true(), 'Delta', 1, 'M', 4);
% Set state cost objective for regulator
lr = @(x, u, xsp, usp, Du) (x - xsp)'*Qr*(x - xsp) + (u - usp)'*Rr*(u - usp) + Du'*Rr*Du;
lr = mpc.getCasadiFunc(lr, [Nx, Nu, Nx, Nu, Nu], {'x', 'u', 'xsp', 'usp', 'Du'}, {'lr'});
% set terminal cost for regulator
Vr = mpc.getCasadiFunc(@(x, xsp) (x - xsp)'*Pr*(x - xsp), [Nx, Nx], ...
                       {'x', 'xsp'}, {'Vr'});
% output function
h = mpc.getCasadiFunc(@(x, Cd, d)output(x) + Cd*d, {Nx, [Ny, Nd], Nd}, {'x', 'Cd', 'd'}, {'h'});
% Build MPC solvers for nonlinear models.
ulb = repmat([0.3; 5], 3, 1);
uub = repmat([1.8; 50], 3, 1);
lbr = struct();
lbr.u = repmat(ulb, 1, Nr);
ubr = struct();
ubr.u = repmat(uub, 1, Nr);
N_reg = struct('x', Nx, 'u', Nu, 't', Nr);
kwargs = struct();
kwargs.N = N_reg;
kwargs.l = lr;
kwargs.Vf = Vr;
kwargs.lb = lbr;
kwargs.ub = ubr;
kwargs.par = struct('xsp', xs, 'usp', us, 'p', p_gass, 'Bd', Bd, 'd', zeros(Nd, 1));
kwargs.uprev = us;
kwargs.guess = struct('x', repmat(xs, 1, Nr + 1), 'u', repmat(us, 1, Nr));
kwargs.verbosity = 0;
regulator = mpc.nmpc('f', ode_reg_casadi, '**', kwargs);
% Build steady-state target finder.
kwargs = struct();
kwargs.N = struct('x', Nx, 'u', Nu, 'y', Ny);
kwargs.lb = struct('u', ulb, 'x', 0.5*xs);
kwargs.ub = struct('u', uub, 'x', 2*xs);
kwargs.h = h;
kwargs.par = struct('p', p_gass, 'Bd', Bd, 'Cd', Cd, 'd', zeros(Nd, 1));
kwargs.verbosity = 0;
sstarg = mpc.sstarg('f', ode_reg_casadi, '**', kwargs);

% Define Casadi functions for estimator.
model_est = @(x, u) ode_est(x, u, par);
ode_est_casadi = mpc.getCasadiFunc(@(x, u, Bd, d)model_est(x, u+[0; 0; 0; Bd*d]), ...
    {Nx, Nu_est, [Nu, Nd], Nd}, {'x', 'u', 'Bd', 'd'}, {'ode_est_casadi'}, 'rk4', ...
    true(), 'Delta', 1, 'M', 4);
Qeinv = mpctools.spdinv(Qe);
Reinv = mpctools.spdinv(Re);
Qdinv = mpctools.spdinv(Qd);
% Set state cost for estimator
le = mpc.getCasadiFunc(@(w, v, Dd) w'*Qeinv*w + v'*Reinv*v + Dd'*Qdinv*Dd,...
    [Nw, Nv, Nd], {'w', 'v', 'Dd'}, {'le'});
% Set arrival cost for estimator
Ve = mpc.getCasadiFunc(@(x, x0bar, d, d0bar, Peinv)([x; d] - [x0bar; d0bar])'*Peinv*([x; d] - [x0bar; d0bar]),...
    {Nx, Nx, Nd, Nd, [Nx + Nd, Nx + Nd]}, {'x', 'x0bar', 'd', 'd0bar' 'Peinv'}, {'Ve'});
% Build MHE solver
N_est = struct('x', Nx, 'd', Nd, 'u', Nu_est, 'y', Ny, 't', Ne);
pars = struct('y', par.nmpc.ysim, 'u', zeros(Nu_est, Ne), 'x0bar', par.nmpc.ini, 'Peinv', mpctools.spdinv(Pe), 'd0bar', zeros(Nd, 1), 'Bd', Bd, 'Cd', Cd);
lbe = struct('x', repmat(0.5*xs, 1, Ne + 1), 'd', repmat(-1e-5*ones(Nd, 1), 1, Ne+1)); 
ube = struct('x', repmat(2*xs, 1, Ne + 1), 'd', repmat(1e-5*ones(Nd, 1), 1, Ne+1));
guess = struct('x', repmat(par.nmpc.ini, 1, Ne + 1));
estmtr = mpc.nmhe('f', ode_est_casadi,'l', le, 'h', h, 'N', N_est, 'lx', Ve, ...
                 'lb', lbe, 'ub', ube, 'par', pars, 'guess', guess, 'verbosity', 0, 'wadditive', true());
switch disturbancemodel
    case 'Good'
        estmtr.ub.d = repmat(50*ones(Nd, 1), 1, Ne+1);
        estmtr.lb.d = repmat(-50*ones(Nd, 1), 1, Ne+1);
end
end

% Nonpulsatile model for estimator
function dxdt = ode_est(x, u, par)
fasf = x(1)*par.Mean.fas_sp/par.Mean.Psp;
% modified baroreceptive firing rate
Pas1 = exp((u(4) - par.stm.Ias1)/par.stm.kas1)./(1 + exp((u(4) - par.stm.Ias1)/par.stm.kas1));
fas1 = (par.stm.Pas0 + par.stm.Pass*u(5) + par.stm.Pasp*fasf)*(u(5) + fasf);
Pas2 = exp((u(6) - par.stm.Ias2)/par.stm.kas2)./(1 + exp((u(6) - par.stm.Ias2)/par.stm.kas2));
fas2 = (par.stm.Pas0 + par.stm.Pass*u(7) + par.stm.Pasp*fasf)*(u(7) + fasf);
Pas3 = exp((u(8) - par.stm.Ias3)/par.stm.kas3)./(1 + exp((u(8) - par.stm.Ias3)/par.stm.kas3));
fas3 = (par.stm.Pas0 + par.stm.Pass*u(9) + par.stm.Pasp*fasf)*(u(9) + fasf);
fas = u(1)*par.stm.C(1, 1)*Pas1*fas1 + u(2)*par.stm.C(1, 2)*Pas2*fas2 + u(3)*par.stm.C(1, 3)*Pas3*fas3 + (1 - u(1)*par.stm.C(1, 1)*Pas1 - u(2)* par.stm.C(1, 2)*Pas2 - u(3)*par.stm.C(1, 3)*Pas3)*fasf;
fesf = par.Mean.fes_max/(1 + max((fas/par.Mean.fas_sp), eps())^par.Mean.kes);
fevf = par.Mean.fev_max/(1 + max((fas/par.Mean.fas_sp), eps())^(-par.Mean.kev));
% modified vagal firing rate 
Pev1 = exp((u(4) - par.stm.Iev1)/par.stm.kev1)./(1 + exp((u(4) - par.stm.Iev1)/par.stm.kev1));
fev1 = (par.stm.Pev0 + par.stm.Pevs*u(5) + par.stm.Pevp*fevf)*(u(5) + fevf);
Pev2 = exp((u(6) - par.stm.Iev2)/par.stm.kev2)./(1 + exp((u(6) - par.stm.Iev2)/par.stm.kev2));
fev2 = (par.stm.Pev0 + par.stm.Pevs*u(7) + par.stm.Pevp*fevf)*(u(7) + fevf);
Pev3 = exp((u(8) - par.stm.Iev3)/par.stm.kev3)./(1 + exp((u(8) - par.stm.Iev3)/par.stm.kev3));
fev3 = (par.stm.Pev0 + par.stm.Pevs*u(9) + par.stm.Pevp*fevf)*(u(9) + fevf);
fev = u(1)*par.stm.C(3, 1)*Pev1*fev1 + u(2)*par.stm.C(3, 2)*Pev2*fev2 + u(3)*par.stm.C(3, 3)*Pev3*fev3 + (1 - u(1)*par.stm.C(3, 1)*Pev1 - u(2)*par.stm.C(3, 2)*Pev2 - u(3)*par.stm.C(3, 3)*Pev3)*fevf;
% modified sympathetic firing rate
Pes1 = exp((u(4) - par.stm.Ies1)/par.stm.kes1)./(1 + exp((u(4) - par.stm.Ies1)/par.stm.kes1));
fes1 = (par.stm.Pes0 + par.stm.Pess*u(5) + par.stm.Pesp*fesf)*(u(5) + fesf);
Pes2 = exp((u(6) - par.stm.Ies2)/par.stm.kes2)./(1 + exp((u(6) - par.stm.Ies2)/par.stm.kes2));
fes2 = (par.stm.Pes0 + par.stm.Pess*u(7) + par.stm.Pesp*fesf)*(u(7) + fesf);
Pes3 = exp((u(8) - par.stm.Ies3)/par.stm.kes3)./(1 + exp((u(8) - par.stm.Ies3)/par.stm.kes3));
fes3 = (par.stm.Pes0 + par.stm.Pess*u(9) + par.stm.Pesp*fesf)*(u(9) + fesf);
fes = u(1)*par.stm.C(2, 1)*fes1*Pes1 + u(2)*par.stm.C(2, 2)*fes2*Pes2 + u(3)*par.stm.C(2, 3)*fes3*Pes3 + (1 - u(1)*par.stm.C(2, 1)*Pes1 - u(2)*par.stm.C(2, 2)*Pes2 - u(3)*par.stm.C(2, 3)*Pes3)*fesf;

dx1dt = 1/par.Mean.Cao*(1/(x(2) + eps())*((x(6) - par.Mean.Cao*x(1))/par.Mean.Cvc/(x(4)+eps()) - x(1)/(x(5) + eps())) - ((par.Mean.Cvc + par.Mean.Cao)*x(1) - x(6))/par.Mean.Cvc/(x(3) + eps()));
ns = fes/par.Mean.fes_max;
nv = fev/par.Mean.fev_max;
dx2dt = (-x(2)+ par.Mean.T0 + par.Mean.G_Ts*ns + par.Mean.G_Tv*nv)/par.Mean.tau_T;
dx3dt = (-x(3)+ par.Mean.R0 + par.Mean.G_R*ns)/par.Mean.tau_R;
dx4dt = (-x(4)+ par.Mean.Ef0 + par.Mean.G_Ef*ns)/par.Mean.tau_Ef;
dx5dt = (-x(5)+ par.Mean.Ee0 + par.Mean.G_Ee*ns)/par.Mean.tau_Ee;
dx6dt = (-x(6)+ par.Mean.V0 + par.Mean.G_V*ns)/par.Mean.tau_V;
dxdt = [dx1dt; dx2dt; dx3dt; dx4dt; dx5dt; dx6dt];
end


% Nonpulsatile model for regulator
function dxdt = ode_reg(x, u, p, par)
fasf = x(1)*par.Mean.fas_sp/par.Mean.Psp;
% modified baroreceptive firing rate
Pas1 = exp((u(1) - par.stm.Ias1)/par.stm.kas1)./(1 + exp((u(1) - par.stm.Ias1)/par.stm.kas1));
fas1 = (par.stm.Pas0 + par.stm.Pass*u(2) + par.stm.Pasp*fasf)*(u(2) + fasf);
Pas2 = exp((u(3) - par.stm.Ias2)/par.stm.kas2)./(1 + exp((u(3) - par.stm.Ias2)/par.stm.kas2));
fas2 = (par.stm.Pas0 + par.stm.Pass*u(4) + par.stm.Pasp*fasf)*(u(4) + fasf);
Pas3 = exp((u(5) - par.stm.Ias3)/par.stm.kas3)./(1 + exp((u(5) - par.stm.Ias3)/par.stm.kas3));
fas3 = (par.stm.Pas0 + par.stm.Pass*u(6) + par.stm.Pasp*fasf)*(u(6) + fasf);
fas = p(1)*par.stm.C(1, 1)*Pas1*fas1 + p(2)*par.stm.C(1, 2)*Pas2*fas2 + p(3)*par.stm.C(1, 3)*Pas3*fas3 + (1 - p(1)*par.stm.C(1, 1)*Pas1 - p(2)* par.stm.C(1, 2)*Pas2 - p(3)*par.stm.C(1, 3)*Pas3)*fasf;
fesf = par.Mean.fes_max/(1 + max((fas/par.Mean.fas_sp), eps())^par.Mean.kes);
fevf = par.Mean.fev_max/(1 + max((fas/par.Mean.fas_sp), eps())^(-par.Mean.kev));
% modified vagal firing rate 
Pev1 = exp((u(1) - par.stm.Iev1)/par.stm.kev1)./(1 + exp((u(1) - par.stm.Iev1)/par.stm.kev1));
fev1 = (par.stm.Pev0 + par.stm.Pevs*u(2) + par.stm.Pevp*fevf)*(u(2) + fevf);
Pev2 = exp((u(3) - par.stm.Iev2)/par.stm.kev2)./(1 + exp((u(3) - par.stm.Iev2)/par.stm.kev2));
fev2 = (par.stm.Pev0 + par.stm.Pevs*u(4) + par.stm.Pevp*fevf)*(u(4) + fevf);
Pev3 = exp((u(5) - par.stm.Iev3)/par.stm.kev3)./(1 + exp((u(5) - par.stm.Iev3)/par.stm.kev3));
fev3 = (par.stm.Pev0 + par.stm.Pevs*u(6) + par.stm.Pevp*fevf)*(u(6) + fevf);
fev = p(1)*par.stm.C(3, 1)*Pev1*fev1 + p(2)*par.stm.C(3, 2)*Pev2*fev2 + p(3)*par.stm.C(3, 3)*Pev3*fev3 + (1 - p(1)*par.stm.C(3, 1)*Pev1 - p(2)*par.stm.C(3, 2)*Pev2 - p(3) *par.stm.C(3, 3)*Pev3)*fevf;
% modified sympathetic firing rate
Pes1 = exp((u(1) - par.stm.Ies1)/par.stm.kes1)./(1 + exp((u(1) - par.stm.Ies1)/par.stm.kes1));
fes1 = (par.stm.Pes0 + par.stm.Pess*u(2) + par.stm.Pesp*fesf)*(u(2) + fesf);
Pes2 = exp((u(3) - par.stm.Ies2)/par.stm.kes2)./(1 + exp((u(3) - par.stm.Ies2)/par.stm.kes2));
fes2 = (par.stm.Pes0 + par.stm.Pess*u(4) + par.stm.Pesp*fesf)*(u(4) + fesf);
Pes3 = exp((u(5) - par.stm.Ies3)/par.stm.kes3)./(1 + exp((u(5) - par.stm.Ies3)/par.stm.kes3));
fes3 = (par.stm.Pes0 + par.stm.Pess*u(6) + par.stm.Pesp*fesf)*(u(6) + fesf);
fes = p(1)*par.stm.C(2, 1)*fes1*Pes1 + p(2)*par.stm.C(2, 2)*fes2*Pes2 + p(3)*par.stm.C(2, 3)*fes3*Pes3 + (1 - p(1)*par.stm.C(2, 1)*Pes1 - p(2)*par.stm.C(2, 2)*Pes2 - p(3)*par.stm.C(2, 3)*Pes3)*fesf;
dx1dt = 1/par.Mean.Cao*(1/(x(2) + eps())*((x(6) - par.Mean.Cao*x(1))/par.Mean.Cvc/(x(4) + eps()) - x(1)/(x(5) + eps())) - ((par.Mean.Cvc + par.Mean.Cao)*x(1) - x(6))/par.Mean.Cvc/(x(3) + eps()));
ns = fes/par.Mean.fes_max;
nv = fev/par.Mean.fev_max;
dx2dt = (-x(2)+ par.Mean.T0 + par.Mean.G_Ts*ns + par.Mean.G_Tv*nv)/par.Mean.tau_T;
dx3dt = (-x(3)+ par.Mean.R0 + par.Mean.G_R*ns)/par.Mean.tau_R;
dx4dt = (-x(4)+ par.Mean.Ef0 + par.Mean.G_Ef*ns)/par.Mean.tau_Ef;
dx5dt = (-x(5)+ par.Mean.Ee0 + par.Mean.G_Ee*ns)/par.Mean.tau_Ee;
dx6dt = (-x(6)+ par.Mean.V0 + par.Mean.G_V*ns)/par.Mean.tau_V;
dxdt = [dx1dt; dx2dt; dx3dt; dx4dt; dx5dt; dx6dt];
end

function y = output(x)
    y = [x(1); x(2)];
end
