global concore;
import_concore;
disp("controllerM.m -- matlab or octave")
disp("uses aux file with function definition: controller.m")
global ysp;
ysp = 3.0;
concore_default_maxtime(150) 
concore.delay = 0.02
init_simtime_u = '[0.0, 0.0]';
init_simtime_ym = '[0.0, 0.0]';
u = concore_initval(init_simtime_u);
while(concore.simtime<concore.maxtime)
    while concore_unchanged()
        ym = concore_read(1, 'ym', init_simtime_ym);      
    end
    %%%%
    u = controller(ym);
    %%%%%
    disp(ym(1))
    disp(u(1))
    concore_write(1, 'u', u, 0);
end
disp("retry=")
disp(concore.retrycount)
