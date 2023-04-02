import concore
import time
import threading

global ymglobal
ymglobal = 0

def extract(ampD):
    s = 0.0
    for data in ampD:
       s += data
    return s/len(ampD)

def acq():
  global ymglobal
  counter = 0
  while(True):
    ampT = []
    ampD = []
    for block in range(numBlocks):
        for frame in range(framesPerBlock):
            ampT.append(counter + block*framesPerBlock+frame)
            ampD.append(counter + abs(frame-framesPerBlock/2))
    print(ampT)
    print(ampD)
    ymglobal = extract(ampD)
    print(ymglobal)
    counter = counter +  numBlocks*framesPerBlock 
    time.sleep(1)

acq_thread = threading.Thread(target=acq, daemon=True)

def cnt():
    count = 0
    while(True):
        print(count)
        count = (count + 1)%10
        time.sleep(1)

#cnt_thread = threading.Thread(target=cnt, daemon=True)

#initialization
numBlocks = 3
framesPerBlock = 5
        
concore.delay = 0.01
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

ym = concore.initval(init_simtime_ym)

#cnt_thread.start()
acq_thread.start()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    ym[0]  = ymglobal 
    print("")
    print("ym="+str(ym[0]));
    concore.write(1,"ym",ym)
print("retry="+str(concore.retrycount))
