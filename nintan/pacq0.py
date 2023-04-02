import concore
import time
import threading

TIME_SAMPLE = 5
global counter
counter = 0


def extract(ampD):
    s = 0.0
    for data in ampD:
       s += data
       time.sleep(TIME_DATA/4) #make extract really slow for testing
    return s/len(ampD)

def acq():
    global counter
    global ampT,ampD
    for block in range(numBlocks):
        for frame in range(framesPerBlock):
            ampT.append(counter + block*framesPerBlock+frame)
            ampD.append(counter + abs(frame-framesPerBlock/2))
            time.sleep(TIME_DATA)
    print(ampT)
    print(ampD)
    counter = counter +  numBlocks*framesPerBlock 

#initialization
numBlocks = 3
framesPerBlock = 5
TIME_DATA = TIME_SAMPLE /(numBlocks*framesPerBlock)
        
concore.delay = 0.01
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

ym = concore.initval(init_simtime_ym)

acq_thread = threading.Thread(target=acq, daemon=True)
nxtacq_thread = threading.Thread(target=acq, daemon=True)
ampT = []
ampD = []
acq_thread.start()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    acq_thread.join()
    acq_thread = nxtacq_thread
    oldAmpD = ampD
    ampT = []
    ampD = []
    acq_thread.start()
    nxtacq_thread = threading.Thread(target=acq, daemon=True)
    ym[0] = extract(oldAmpD)
    print("ym="+str(ym[0]));
    concore.write(1,"ym",ym)
acq_thread.join()
print("retry="+str(concore.retrycount))
