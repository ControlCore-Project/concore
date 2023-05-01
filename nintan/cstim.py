import concore
from ast import literal_eval
import time

try:
    bangbang = concore.params['bang']
except:
    bangbang = False
    
try:
    freq_control = concore.params['freq_control']
except:
    freq_control = False
    
concore.delay = 0.01
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"
minElasped = 10000000
maxElasped = 0
sumElasped  = 0
u = concore.initval(init_simtime_u)
wallclock1 = time.perf_counter()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
        
    if freq_control:
        u[0] = abs(ym[1])/100.0
        if abs(ym[1]) > 100:
            u[0] = 1.0
        elif abs(ym[1]) < 1:
            u[0] = 0.01
            
    elif bangbang:
        if ym[0] > 0:
            u[0] = 0.9
        else:
            u[0] = 0.1
    else:
        try:
            u[0] = float(literal_eval(input()))
        except:
            print("bad input, using .5 instead")
            u[0] = 0.5        
    print("ym="+str(ym[0])+" u="+str(u[0]));
    print("min="+str(minElasped))
    print("avg="+str(sumElasped/max(1,concore.simtime)))
    print("max="+str(maxElasped))
    concore.write(1,"u",u);
    wallclock2 = time.perf_counter()
    elasped = wallclock2-wallclock1
    sumElasped += elasped
    wallclock1 = wallclock2
    minElasped = min(minElasped, elasped)
    maxElasped = max(maxElasped, elasped)
 
print("retry="+str(concore.retrycount))
print("min="+str(minElasped))
print("avg="+str(sumElasped/concore.maxtime))
print("max="+str(maxElasped))
