import time
from ast import literal_eval

try:
    iport = literal_eval(open("concore.iport").read())
except:
    iport = dict()
try:
    oport = literal_eval(open("concore.oport").read())
except:
    oport = dict()


s = ''
olds = ''
delay = 1
retrycount = 0
inpath = "/in"  #must be abs path for docker
outpath = "/out"

#9/17/22
try:
    params = literal_eval(open(inpath+"1/concore.params").read())
except:
    params = dict()
#9/12/21
def default_maxtime(default):
    global maxtime
    try:
        maxtime = literal_eval(open(inpath+"1/concore.maxtime").read())
    except:
        maxtime = default 
default_maxtime(100)

def unchanged():
    global olds,s
    if olds==s:
        s = ''
        return True
    else:       
        olds = s       
        return False

def read(port, name, initstr):
    global s,simtime,retrycount
    time.sleep(delay)
    try:
        infile = open(inpath+str(port)+"/"+name);
        ins = infile.read()
    except:
        ins = initstr
    while len(ins)==0:
        time.sleep(delay)
        ins = infile.read()
        retrycount += 1
    s += ins
    inval = literal_eval(ins)
    simtime = max(simtime,inval[0])
    return inval[1:]

def write(port, name, val, delta=0):
    global outpath,simtime
    if isinstance(val,str):
        time.sleep(2*delay)
    elif isinstance(val,list)==False:
        print("mywrite must have list or str")
        quit() 
    try:
        with open(outpath+str(port)+"/"+name,"w") as outfile:     
            if isinstance(val,list):
                outfile.write(str([simtime+delta]+val))
                simtime += delta
            else:
                outfile.write(val)
    except:
        print("skipping"+outpath+str(port)+"/"+name);

def initval(simtime_val):
    global simtime
    val = literal_eval(simtime_val)
    simtime = val[0]
    return val[1:]

