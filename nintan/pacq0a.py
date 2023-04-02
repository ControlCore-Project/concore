import concore
import time
import threading

global ymglobal,counter
ymglobal = 0
counter = 0

def extract(ampD):
    s = 0.0
    for data in ampD:
       s += data
    return s/len(ampD)

def acq():
    global ymglobal,counter
    ampT = []
    ampD = []
    for block in range(numBlocks):
        for frame in range(framesPerBlock):
            ampT.append(counter + block*framesPerBlock+frame)
            ampD.append(counter + abs(frame-framesPerBlock/2))
    print(ampT)
    print(ampD)
    ymglobal = extract(ampD)
    print("ymglobal="+str(ymglobal))
    counter = counter +  numBlocks*framesPerBlock 
    time.sleep(5)

#initialization
numBlocks = 3
framesPerBlock = 5
        
concore.delay = 0.01
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

ym = concore.initval(init_simtime_ym)

acq_thread = threading.Thread(target=acq, daemon=True)
nxtacq_thread = threading.Thread(target=acq, daemon=True)
acq_thread.start()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    acq_thread.join()
    ym[0]  = ymglobal 
    acq_thread = nxtacq_thread
    acq_thread.start()
    nxtacq_thread = threading.Thread(target=acq, daemon=True)
    print("")
    print("ym="+str(ym[0]));
    concore.write(1,"ym",ym)
acq_thread.join()
print("retry="+str(concore.retrycount))
