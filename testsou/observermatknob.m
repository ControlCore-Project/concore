% observer
% this version runs on matlab or octave 4/4/21, 4/9/21 with concore_initval
% changes:
%   a) separated each concore_ function to its own file so that octave/matlab
%      automatically defines before starting to run this script
%   b) changed "..." to '...' (octave doesn't care, but matlab does)
%   c) changed fputs(f,v) to fprintf(f,'%s',v)  (matlab doesn't have fputs)
%   d) import_concore does initialization (and writes concorekill.bat)

global concore;
import_concore;

disp("observer of knob matlab or octave")
concore.retrycount = 0;
concore.delay=0.01;
%Nsim=100;
concore_default_maxtime(100);
pmstate = 0;
init_simtime_knob = '[0,10000]';
init_simtime_ym = '[0,0,0]';
ym = concore_initval(init_simtime_ym);
knob = concore_initval(init_simtime_knob);

while(concore.simtime<concore.maxtime)
    while concore_unchanged()
        ym = concore_read(1, 'ym', init_simtime_ym);      
    end
    disp(ym);
    if (concore.simtime > concore.maxtime/2)
      knob(1) = 20000;
      concore_write(1, 'knob', knob, 0);
    end
end

disp("retry=")
disp(concore.retrycount)

