import concore
import time
import threading

TIME_SAMPLE = 5
global counter
counter = 0


def extract(amplifierData):
    s = 0.0
    for data in amplifierData:
       s += data
       time.sleep(TIME_DATA/4) #make extract really slow for testing
    return s/len(amplifierData)

def acq():
    global counter
    global amplifierTimestamps,amplifierData
    for block in range(numBlocks):
        for frame in range(framesPerBlock):
            amplifierTimestamps.append(counter + block*framesPerBlock+frame)
            amplifierData.append(counter + abs(frame-framesPerBlock/2))
            time.sleep(TIME_DATA)
    print(amplifierTimestamps)
    print(amplifierData)
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
amplifierTimestamps = []
amplifierData = []
acq_thread.start()
while(concore.simtime<concore.maxtime):
    while concore.unchanged():
        ym = concore.read(1,"ym",init_simtime_ym)
    acq_thread.join()
    acq_thread = nxtacq_thread
    oldAmpD = amplifierData
    amplifierTimestamps = []
    amplifierData = []
    acq_thread.start()
    nxtacq_thread = threading.Thread(target=acq, daemon=True)
    ym[0] = extract(oldAmpD)
    print("ym="+str(ym[0]));
    concore.write(1,"ym",ym)
acq_thread.join()
print("retry="+str(concore.retrycount))
