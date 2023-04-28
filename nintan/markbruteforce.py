import utils_concore 
import numpy as np
import matplotlib.pyplot as plt
import concore

FREQ_BINS = 25

def brute_freqs(filename):
    y, yextra2, yextra3 = utils_concore.read_trellis_data([filename+'.nf3'],channums=[1,2,3,4])  
    plt.figure()
    plt.subplot(411)
    plt.plot(range(len(y[0])),y[0])
    #plt.xlabel('Gastric 1')
    plt.subplot(412)
    plt.plot(range(len(y[1])),y[1])
    #plt.xlabel('Gastric 2')
    plt.subplot(413)
    plt.plot(range(len(y[2])),y[2])
    #plt.xlabel('Gastric 3')
    plt.subplot(414)
    plt.plot(range(len(y[3])),y[3])
    plt.xlabel('Raw file:'+filename+ ' iteration '+str(concore.simtime))
    plt.savefig(filename+str(concore.simtime)+"r.pdf")

    result = []
    plt.figure()
    plt.subplot(411)
    result.append(smooth_freq(y,0,FREQ_BINS))
    plt.subplot(412)
    result.append(smooth_freq(y,1,FREQ_BINS))
    plt.subplot(413)
    result.append(smooth_freq(y,2,FREQ_BINS))
    plt.subplot(414)
    result.append(smooth_freq(y,3,FREQ_BINS))
    plt.xlabel('Freq:'+filename+ ' iteration '+str(concore.simtime))
    plt.savefig(filename+str(concore.simtime)+"f.pdf")
    #plt.show()
    return result

def smooth_freq(y,chan,bins):
    f=np.fft.fft(y[chan])
    f0=np.abs(f[-(bins-1):-1])
    f1=np.abs(f[-bins:-2])
    f2=np.abs(f[-(bins+1):-3])
    fa=f2+2*f1+f2
#    plt.plot(np.arange(bins,2,-1),np.log(np.abs(fa)))
    return bins-np.argmax((np.abs(fa)))


