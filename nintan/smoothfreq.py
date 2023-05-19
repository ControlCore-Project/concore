import numpy as np

def smooth_freq(y,bins):
    f=np.fft.fft(y)
    f0=np.abs(f[-(bins-1):-1])
    f1=np.abs(f[-bins:-2])
    f2=np.abs(f[-(bins+1):-3])
    fa=f2+2*f1+f2
    return bins-np.argmax((np.abs(fa)))

def dom_freq(y,t):
    ttot = (t[-1] - t[0]) * len(y)/(len(y)-1)
    f = np.fft.fft(y)
    fi = np.argmax((np.abs(f)))
    return np.fft.fftfreq(len(y))[fi]*len(y)/ttot
