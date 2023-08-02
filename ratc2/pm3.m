global concore;
import_concore;

%clear all
load('plantData.mat')
ini = par.ini;
concore.retrycount = 0;
concore.delay=0.01;
init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]";
concore_default_maxtime(150);
Nsim = concore.maxtime;
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
    %set disturbance (optional)
    if (concore.simtime == round(Nsim/3))
        par.efrt.G_Rsu = par.efrt.G_Rsu * 0.5;                
        par.efrt.G_Ts = par.efrt.G_Ts * 2.5; 
    end
    [ini, ym] = plant(u, ones(3, 1), 1, ini, par);
    ym(2) = 60/ym(2); %11/23/21 MGA: convert period to HR
    disp(u)
    disp(ym)
    %%%%%%%%%%%
    concore_write(1,'ym',ym',1);
end
disp("retry=")
disp(concore.retrycount)