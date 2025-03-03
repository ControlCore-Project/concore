import time
import os
from ast import literal_eval
import sys
import re

#if windows, create script to kill this process 
# because batch files don't provide easy way to know pid of last command
# ignored for posix!=windows, because "concorepid" is handled by script
# ignored for docker (linux!=windows), because handled by docker stop
if hasattr(sys, 'getwindowsversion'):
    with open("concorekill.bat","w") as fpid:
        fpid.write("taskkill /F /PID "+str(os.getpid())+"\n")

def safe_literal_eval(filename, defaultValue):
    try:
        with open(filename, "r") as file:
            return literal_eval(file.read())
    except (FileNotFoundError, SyntaxError, ValueError, Exception) as e:
        print(f"Error reading {filename}: {e}")
        return defaultValue
    
iport = safe_literal_eval("concore.iport", {})
oport = safe_literal_eval("concore.oport", {})

s = ''
olds = ''
delay = 1
retrycount = 0
inpath = "./in" #must be rel path for local
outpath = "./out"
simtime = 0

#9/21/22
try:
    sparams = open(inpath+"1/concore.params").read()
    if sparams[0] == '"':  #windows keeps "" need to remove
        sparams = sparams[1:]
        sparams = sparams[0:sparams.find('"')]
    if sparams != '{':
        print("converting sparams: "+sparams)
        sparams = "{'"+re.sub(';',",'",re.sub('=',"':",re.sub(' ','',sparams)))+"}"
        print("converted sparams: " + sparams)
    try:
        params = literal_eval(sparams)
    except:
        print("bad params: "+sparams)
except:
    params = dict()
#9/30/22
def tryparam(n, i):
    return params.get(n, i)


#9/12/21
def default_maxtime(default):
    global maxtime
    maxtime = safe_literal_eval(os.path.join(inpath + "1", "concore.maxtime"), default)

default_maxtime(100)

def unchanged():
    global olds, s
    if olds == s:
        s = ''
        return True
    olds = s
    return False

def read(port, name, initstr):
    global s, simtime, retrycount
    max_retries=5
    time.sleep(delay)
    file_path = os.path.join(inpath+str(port), name)

    try:
        with open(file_path, "r") as infile:
            ins = infile.read()
    except FileNotFoundError:
        print(f"File {file_path} not found, using default value.")
        ins = initstr
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return initstr

    attempts = 0
    while len(ins) == 0 and attempts < max_retries:
        time.sleep(delay)
        try:
            with open(file_path, "r") as infile:
                ins = infile.read()
        except Exception as e:
            print(f"Retry {attempts + 1}: Error reading {file_path} - {e}")
        attempts += 1
        retrycount += 1

    if len(ins) == 0:
        print(f"Max retries reached for {file_path}, using default value.")
        return initstr

    s += ins
    try:
        inval = literal_eval(ins)
        simtime = max(simtime, inval[0])
        return inval[1:]
    except Exception as e:
        print(f"Error parsing {ins}: {e}")
        return initstr


def write(port, name, val, delta=0):
    global simtime
    file_path = os.path.join(outpath+str(port), name)

    if isinstance(val, str):
        time.sleep(2 * delay)
    elif not isinstance(val, list):
        print("write must have list or str")
        return

    try:
        with open(file_path, "w") as outfile:
            if isinstance(val, list):
                outfile.write(str([simtime + delta] + val))
                simtime += delta
            else:
                outfile.write(val)
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

def initval(simtime_val):
    global simtime
    try:
        val = literal_eval(simtime_val)
        simtime = val[0]
        return val[1:]
    except Exception as e:
        print(f"Error parsing simtime_val: {e}")
        return []
