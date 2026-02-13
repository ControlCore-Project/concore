import time
import os
from ast import literal_eval
import sys

#if windows, create script to kill this process 
# because batch files don't provide easy way to know pid of last command
# ignored for posix!=windows, because "concorepid" is handled by script
# ignored for docker (linux!=windows), because handled by docker stop
if hasattr(sys, 'getwindowsversion'):
    with open("concorekill.bat","w") as fpid:
        fpid.write("taskkill /F /PID "+str(os.getpid())+"\n")

try:
    with open("concore.iport") as f:
        iport = literal_eval(f.read())
except:
    iport = dict()
try:
    with open("concore.oport") as f:
        oport = literal_eval(f.read())
except:
    oport = dict()



s = ''
olds = ''
delay = 1
retrycount = 0
inpath = "./in" #must be rel path for local
outpath = "./out"

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
        with open(inpath+str(port)+"/"+name) as infile:
            ins = infile.read()
            while len(ins)==0:
                time.sleep(delay)
                ins = infile.read()
                retrycount += 1
    except:
        ins = initstr
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
            else:
                outfile.write(val)
    except:
        print("skipping"+outpath+str(port)+"/"+name);

def initval(simtime_val):
    global simtime
    val = literal_eval(simtime_val)
    simtime = val[0]
    return val[1:]

