%
% abs paths /in and /out for docker
%
disp("cmat")
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
            input1 = fopen("/in1/ym"); 
            s = fscanf(input1,'%c');
            fclose(input1);
        catch exc
            s = init_simtime_ym;
        end     
    end
    while length(s) == 0
        pause(delay);
        input1 = fopen("/in1/ym"); 
        s = fscanf(input1,'%c');
        fclose(input1);
        retrycount = retrycount + 1;
    end
    olds = s;
    ym = eval(s);
    simtime = ym(1);
    ym = ym(2:length(ym));
    u(1) = ym(1)+1;
    %pmstate = pmstate + 1
    %ym(2) = pmstate
    disp(ym(1))
    disp(u(1))
    output1 = fopen("/out1/u","w");
    outstr = cat(2,"[",num2str(simtime),num2str(u,",%e"),"]");
    fputs(output1,outstr);
    fclose(output1);
end

pause(delay);
output1 = fopen("/out1/u","w");
fputs(output1,init_simtime_u);
fclose(output1);
disp("retry=")
disp(retrycount)
