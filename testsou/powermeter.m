%
% this version runs on matlab or octave 4/4/21, 4/9/21 with concore_initval
% changes:
%   a) separated each concore_ function to its own file so that octave/matlab
%      automatically defines before starting to run this script
%   b) changed "..." to '...' (octave doesn't care, but matlab does)
%   c) changed fputs(f,v) to fprintf(f,'%s',v)  (matlab doesn't have fputs)
%   d) import_concore does initialization (and writes concorekill.bat)

global concore;
import_concore;

disp("powermeter matlab or octave")
concore.retrycount = 0;
concore.delay=0.01;
concore_default_maxtime(100);
%Nsim=100;
%init_simtime_u = '[0,0,0]';
%init_simtime_ym = '[0,0,0]';
%init_simtime_u = '[0.0, 0.0, 0.0]';
%init_simtime_ym = '[0.0, 0.0, 0.0]';
init_simtime_u = '[0,0.000000e+00,0.000000e+00]';
init_simtime_ym = '[0,0.000000e+00,0.000000e+00]';
energy = 0
u = concore_initval(init_simtime_u);
ym = concore_initval(init_simtime_ym);

while(concore.simtime<concore.maxtime)
    while concore_unchanged()
        u = concore_read(concore_iport('VC'),'u',init_simtime_u);
    end
    concore_write(concore_oport('VXP'),'u',u,0);
    while concore_unchanged()
        ym = concore_read(concore_iport('VP'),'ym',init_simtime_ym);
    end
    concore_write(concore_oport('VXC'),'ym',ym,0);
    disp('powermeter');
    disp(u(1))
    disp(ym(1))
end
disp("retry=")
disp(concore.retrycount)
