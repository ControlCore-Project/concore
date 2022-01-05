#PW
import concore
import requests
import time
from ast import literal_eval
import os

#time.sleep(7)
timeout_max=20
concore.delay = 0.02

try:
    apikey=open(concore.inpath+'1/concore.apikey',newline=None).readline().rstrip()
except:
    try:
        #perhaps this should be removed for security
        apikey=open('./concore.apikey',newline=None).readline().rstrip()
    except:
        apikey = ''

try:
    yuyu=open(concore.inpath+'1/concore.yuyu',newline=None).readline().rstrip()
except:
    try:
        yuyu=open('./concore.yuyu',newline=None).readline().rstrip()
    except:
        yuyu = 'yuyu'

try:
    name1=open(concore.inpath+'1/concore.name1',newline=None).readline().rstrip()
except:
    try:
        name1=open('./concore.name1',newline=None).readline().rstrip()
    except:
        name1 = 'u'

try:
    name2=open(concore.inpath+'1/concore.name2',newline=None).readline().rstrip()
except:
    try:
        name2=open('./concore.name2',newline=None).readline().rstrip()
    except:
        name2 = 'ym'

try:
    init_simtime_u = open(concore.inpath+'1/concore.init1',newline=None).readline().rstrip()
except:
    try:
        init_simtime_u = open('./concore.init1',newline=None).readline().rstrip()
    except:
        init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"

with open("./"+name1,"w") as fcopy:
    fcopy.write(init_simtime_u)

try:
    init_simtime_ym = open(concore.inpath+'1/concore.init2',newline=None).readline().rstrip()
except:
    try:
        init_simtime_ym = open('./concore.init2',newline=None).readline().rstrip()
    except:
        init_simtime_ym = "[0.0, 0.0, 0.0]"

print(apikey)
print(yuyu)
print(name1+'='+init_simtime_u)
print(name2+'='+init_simtime_ym)

while not os.path.exists(concore.inpath+'1/'+name2):
    time.sleep(concore.delay)

#Nsim = 150
concore.default_maxtime(150)
#init_simtime_u = "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
#init_simtime_ym = "[0.0, 0.0, 0.0]"

u = concore.initval(init_simtime_u)
oldu = init_simtime_u
oldt = 0

#initfiles = {'file1': open('./u', 'rb'), 'file2': open('./ym', 'rb')}
#initfiles = {'file1': open('./u', 'rb'), 'file2': open(concore.inpath+'1/ym', 'rb')}
initfiles = {'file1': open('./'+name1, 'rb'), 'file2': open(concore.inpath+'1/'+name2, 'rb')}
# POST Request to /init with u as file1 and ym as file2
r = requests.post('http://www.controlcore.org/init/'+yuyu+apikey, files=initfiles)


while(concore.simtime<concore.maxtime):
    print("PW outer loop")
    while concore.unchanged():
        ym = concore.read(1,name2,init_simtime_ym)
    f = {'file1': open(concore.inpath+'1/'+name2, 'rb')}
    print("PW: before post ym="+str(ym))
    r = requests.post('http://www.controlcore.org/ctl/'+yuyu+apikey+'&fetch='+name1, files=f,timeout=timeout_max)
    if r.status_code!=200:
        print("bad POST request "+str(r.status_code))
        quit()
    if len(r.text)!=0:
        try:
            t=literal_eval(r.text)[0]
        except:
            print("bad eval "+r.text)
    timeout_count = 0
    t1 = time.perf_counter()
    print("PW: after post status="+str(r.status_code)+" r.content="+str(r.content)+"/"+r.text)
    #while r.text==oldu or len(r.content)==0:
    while oldt==t or len(r.content)==0:
        time.sleep(concore.delay)
        print("PW waiting status="+str(r.status_code)+" content="+ r.content.decode('utf-8')+" t="+str(t))
        f = {'file1': open(concore.inpath+'1/'+name2, 'rb')}
        try:
            r = requests.post('http://www.controlcore.org/ctl/'+yuyu+apikey+'&fetch='+name1, files=f,timeout=timeout_max)
        except:
            print("PW: bad requests")
        timeout_count += 1
        if r.status_code!=200 or time.perf_counter()-t1 > 1.1*timeout_max: #timeout_count>200:
            print("timeout or bad POST request "+str(r.status_code))
            quit()
        if len(r.text)!=0:
            try:
                t=literal_eval(r.text)[0]
            except:
                print("bad eval "+r.text)
    oldt = t
    oldu = r.text
    print("PW: oldu="+oldu+" t="+str(concore.simtime))
    concore.write(1,name1,oldu)
#concore.write(1,"u",init_simtime_u)
print("retry="+str(concore.retrycount))
