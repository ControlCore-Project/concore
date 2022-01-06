%
% no longer abs path for docker /in and /out
disp("pmmat")
retrycount = 0;
delay=0.01;
Nsim=100;
pmstate = 0;
init_simtime_u = "[0,0,0]";
init_simtime_ym = "[0,0,0]";
s = "";
olds = "";
u = eval(init_simtime_u);
simtime = u(1);
u = u(2:length(u));
ym = eval(init_simtime_ym);
simtime = ym(1);
ym = ym(2:length(ym));
while(simtime<Nsim)
    while isequal(olds,s)
        pause(delay);
        try
            input1 = fopen("in1/u"); 
            s = fscanf(input1,'%c');
            fclose(input1);
        catch exc
            s = init_simtime_u;
        end
    end
    while length(s) == 0
        pause(delay);
        input1 = fopen("in1/u"); 
        s = fscanf(input1,'%c');
        fclose(input1);
        retrycount = retrycount + 1;
    end
    olds = s;
    u = eval(s);
    simtime = u(1);
    u = u(2:length(u));
    ym(1) = u(1)+10000;
    %pmstate = pmstate + 1
    %ym(2) = pmstate
    disp(u(1))
    disp(ym(1))
    output1 = fopen("out1/ym","w");
    outstr = cat(2,"[",num2str(simtime+1),num2str(ym,",%e"),"]");
    fputs(output1,outstr);
    fclose(output1);
end

pause(delay);
output1 = fopen("out1/ym","w");
fputs(output1,init_simtime_ym);
fclose(output1);
disp("retry=")
disp(retrycount)
