global concore;
import_concore;

%clear all
load('plantData.mat')
% initialize model constant and variables                                            
ini = [152.273; 7.2261; 5.492; 225.6881; 0; 0.1855; 0.0441; 0.1359; 0.1532; 0.2404; 1.2876; 3.1829; 917.1178];
% initialize MPC constant and variables
%Nsim = 100;                          % number of cardiac cycles
% pl = ones(3, 1);                   % Discrete inputs
% x0 = zeros(Data.input.Nx, 1);       % initial state of the model in MPC
% Pd = Data.input.Pd;                 % variance of estimated states
% u = Data.op1.us;  %overwritten?     
% N = 1;           

concore.retrycount = 0;
concore.delay=0.01;
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]";
concore_default_maxtime(150);
Nsim=concore.maxtime;
init_simtime_ym = "[0.0, 0.0, 0.0]";
u = concore_initval(init_simtime_u)';
ym = concore_initval(init_simtime_ym)';
disp(u)
disp(ym)
while(concore.simtime<Nsim)
    while concore_unchanged()
        u = concore_read(1,'u',init_simtime_u)';
    end
    %%%%%%%%%%%
    [ini, ym] = plant(u, ones(3, 1), 1, ini, par);
    ym(2) = 60/ym(2); %11/23/21 MGA: convert period to HR
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
