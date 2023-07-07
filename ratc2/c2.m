global concore;
import_concore;
GENERATE_PLOT = 0;
% initialize MPC constant and variables
[regulator, sstarg, estmtr] = NMPC_initialization();
xsp = zeros(6, 8);
usp = zeros(6, 8);
status = zeros(8, 1);
% initialize MPC constant and variables
%Nsim = 100;                          % number of cardiac cycles
%pl = ones(3, 1);                   % Discrete inputs
% x0 = zeros(Data.input.Nx, 1);       % initial state of the model in MPC
% Pd = Data.input.Pd;                 % variance of estimated states
% u = Data.op1.us;  %overwritten?     
%N = 1;           
% set matrix to record inputs and outputs
ut = [];
ymt = []; 

concore.retrycount = 0;
concore.delay=0.01;
% setpoint for tracking problem
concore_default_maxtime(150);
Nsim=concore.maxtime;
ysp = repmat([116.04; 60/384.22], 1, Nsim + 1);
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]";
init_simtime_ym = "[0.0, 0.0, 0.0]";
u = concore_initval(init_simtime_u)';
ym = concore_initval(init_simtime_ym)';
pl = zeros(3, 1);

while(concore.simtime<Nsim)
    while concore_unchanged()
        ym = concore_read(1,'ym',init_simtime_ym)';
    end
    ym(2) = 60/ym(2); %11/23/21 MGA: convert HR to period
    %%%%%%%%%%%
    [u, pl, status, xsp, usp] = NMPC(1+concore.simtime, ym, u, pl, ysp, status, xsp, usp, regulator, sstarg, estmtr);
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

%note changed to "1:Nsim" to have same vector length
if GENERATE_PLOT == 1
figure()
hold on
plot(1:Nsim, ymt(1, 1:Nsim))
plot(1:Nsim, repmat(ysp(1), 1, Nsim))
hold off
figure()
hold on
plot(1:Nsim, ymt(2, 1:Nsim))
plot(1:Nsim, repmat(ysp(2), 1, Nsim))
hold off
figure()
subplot 321
plot(1:Nsim, ut(1, 1:Nsim))
subplot 322
plot(1:Nsim, ut(2, 1:Nsim))
subplot 323
plot(1:Nsim, ut(3, 1:Nsim))
subplot 324
plot(1:Nsim, ut(4, 1:Nsim))
subplot 325
plot(1:Nsim, ut(5, 1:Nsim))
subplot 326
plot(1:Nsim, ut(6, 1:Nsim))
% save('')
csvwrite('ytm.csv',ymt)
csvwrite('ut.csv',ut)
pause(20)
end
