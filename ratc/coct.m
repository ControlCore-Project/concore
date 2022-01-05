global concore;
import_concore;
GENERATE_PLOT = 0;
load('ssm6nov.mat')
% initialize MPC constant and variables
%Nsim = 100;                          % number of cardiac cycles
%pl = ones(3, 1);                   % Discrete inputs
x0 = zeros(Data.input.Nx, 1);       % initial state of the model in MPC
Pd = Data.input.Pd;                 % variance of estimated states
u = Data.op1.us;  %overwritten?     
%N = 1;           
% set matrix to record inputs and outputs
ut = [];
ymt = []; 

concore.retrycount = 0;
concore.delay=0.01;
concore_default_maxtime(150);
Nsim=concore.maxtime;
init_simtime_u = "[0,0,0,0,0,0,0]";
init_simtime_ym = "[0,0,0]";
u = concore_initval(init_simtime_u)';
ym = concore_initval(init_simtime_ym)';

while(concore.simtime<Nsim)
    while concore_unchanged()
        ym = concore_read(1,'ym',init_simtime_ym)';
    end
    %%%%%%%%%%%
    [u, x0, Pd] = MPC(u, x0, ym, Data, Pd);
    ut(:, concore.simtime+1) = u;
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
plot(1:Nsim, repmat(Data.op1.ysp(1), 1, Nsim))
hold off
figure()
hold on
plot(1:Nsim, ymt(2, 1:Nsim))
plot(1:Nsim, repmat(Data.op1.ysp(2), 1, Nsim))
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
save('')
csvwrite('ytm.csv',ymt)
csvwrite('ut.csv',ut)
pause(20)
end
