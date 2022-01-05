global concore;
import_concore;

%clear all
load('ssm6nov.mat')
% initialize model constant and variables                                            
ini = [217.77; 4.42; 108.84; 92.08; 0.17; 0.04; 0.13; 0.15; 0.12; 1.94; 0];     % initial conditions
% initialize MPC constant and variables
%Nsim = 100;                          % number of cardiac cycles
pl = ones(3, 1);                   % Discrete inputs
%x0 = zeros(Data.input.Nx, 1);       % initial state of the model in MPC
%Pd = Data.input.Pd;                 % variance of estimated states
u = Data.op1.us;  %overwritten?     
N = 1;           

concore.retrycount = 0;
concore.delay=0.01;
init_simtime_u = "[0,0,0,0,0,0,0]";
concore_default_maxtime(150);
Nsim=concore.maxtime;
init_simtime_ym = "[0,0,0]";
u = concore_initval(init_simtime_u)';
ym = concore_initval(init_simtime_ym)';

while(concore.simtime<Nsim)
    while concore_unchanged()
        u = concore_read(1,'u',init_simtime_u)';
    end
    %%%%%%%%%%%
    [ini, HR, MAP] = plant(u, pl, N, ini, par);
    ym = [MAP; HR];

    disp(u)
    disp(ym)
    %%%%%%%%%%%
    concore_write(1,'ym',ym',1);
end
disp("retry=")
disp(concore.retrycount)

% start MPC
%for i = 1:Nsim
%    ut(:, i) = uc;
%    [ini, HR, MAP] = plant(uc, pl, N, ini, par);
%    ym = [MAP; HR];
%    ymt(:,i) = ym;
%    [uc, x0, Pd] = MPC(uc, x0, ym, Data, Pd);
%end
