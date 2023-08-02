global concore;
import_concore;
% initialize MPC constant and variables
disturbancemodel = 'Good'; % 'No'/'Good'
[regulator, sstarg, estmtr] = NMPC_initialization(disturbancemodel);
Ne = 10;    % estimation horizon
Nd = 8;     % disturbance dimension (input + output)
xsp = zeros(6, 8);
usp = zeros(6, 8);
status = zeros(8, 1);
xprior = repmat([169.2; 0.14; 0.7457;0.15;5.41;668.56], 1, Ne);
dprior = zeros(Nd, Ne); 
pl = zeros(3, 1);
% set matrix to record inputs and outputs
ut = [];
ymt = []; 

concore.retrycount = 0;
concore.delay=0.01;
% setpoint for tracking problem
concore_default_maxtime(150);
Nsim = concore.maxtime;
ysp = repmat([116.04; 60/384.22], 1, Nsim + 1);
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]";
init_simtime_ym = "[0.0, 0.0, 0.0]";
u = concore_initval(init_simtime_u)';
ym = concore_initval(init_simtime_ym)';

while(concore.simtime < Nsim)
    while concore_unchanged()
        ym = concore_read(1,'ym',init_simtime_ym)';
    end
    ym(2) = 60/ym(2); %11/23/21 MGA: convert HR to period
    %%%%%%%%%%%
    [u, pl, status, xsp, usp, xprior, dprior] = NMPC(1 + concore.simtime, ...
        ym, u, pl, ysp, status, xsp, usp, xprior, dprior, regulator, sstarg, estmtr, disturbancemodel);
    ut(:, concore.simtime+1) = u;
    ym(2) = 60/ym(2); %11/23/21 MGA: convert period back to HR for plot
    ymt(:,concore.simtime+1) = ym;
    disp(concore.simtime)
    disp(u)
    disp(ym)
    %%%%%%%%%%%
    concore_write(1,'u',u',0);
end
disp("retry=")
disp(concore.retrycount)


