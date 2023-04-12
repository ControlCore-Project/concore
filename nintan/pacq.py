# acq and init taken from: https://intantech.com/files/RHX_TCP.zip
# In order to run this example script successfully, the Intan RHX software
# should first be started, and through Network -> Remote TCP Control:
# Command Output should open a connection at 127.0.0.1, Port 5000.
# Status should read "Pending"
# Waveform Output (in the Data Output tab) should open a connection at 127.0.0.1, Port 5001.
# Status should read "Pending" for the Waveform Port (Spike Port is unused for this example,
# and can be left disconnected)
# Once these ports are opened, this script can be run to acquire ~1 second of wideband data from channel A-010,

import concore
import time
import threading
import socket
import matplotlib.pyplot as plt

try:
    showPlot = concore.params['plot']
except:
    showPlot = 0

try:
    tsamp = concore.params['tsamp']
    if tsamp > 1:
       tsamp = 1
except:
    tsamp = 1 

def validseq(t):
    for i in range(0,len(t)-1):
        if t[i] >= t[i+1]:
             print('i='+str(i)+': '+str(t[i])+'>='+str(t[i+1]))

def extract(amplifierData):
    s = 0.0
    for data in amplifierData:
       s += data
       #time.sleep(0.5/len(amplifierData)) #make extract really slow for testing
    return s/len(amplifierData)

def readUint32(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 4]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=False)
    arrayIndex = arrayIndex + 4
    return variable, arrayIndex

def readInt32(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 4]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=True)
    arrayIndex = arrayIndex + 4
    return variable, arrayIndex

def readUint16(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 2]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=False)
    arrayIndex = arrayIndex + 2
    return variable, arrayIndex

def clearall():
    # Clear TCP data output to ensure no TCP channels are enabled
    scommand.sendall(b'execute clearalldataoutputs')
    time.sleep(0.1)
    # Send TCP commands to set up TCP Data Output Enabled for wide
    # band of channel A-010
    scommand.sendall(b'set a-010.tcpdataoutputenabled true')
    time.sleep(0.1)


def acq():
    # Run controller for tsamp second
    scommand.sendall(b'set runmode run')
    time.sleep(tsamp)
    scommand.sendall(b'set runmode stop')

    # Read waveform data
    rawData = swaveform.recv(WAVEFORM_BUFFER_SIZE)
    if len(rawData) % waveformBytesPerBlock != 0:
        raise Exception('unexpected amount of data')
    numBlocks = int(len(rawData) / waveformBytesPerBlock)

    rawIndex = 0 # Index used to read the raw data 

    for block in range(numBlocks):
        # Expect 4 bytes to be TCP Magic Number as uint32.
        # If not what's expected, raise an exception.
        magicNumber, rawIndex = readUint32(rawData, rawIndex)
        if magicNumber != 0x2ef07a08:
            raise Exception('Error... magic number incorrect')

        # Each block should contain 128 frames of data - process each
        # of these one-by-one
        for frame in range(framesPerBlock):
            # Expect 4 bytes to be timestamp as int32.
            rawTimestamp, rawIndex = readInt32(rawData, rawIndex)
            
            # Multiply by 'timestep' to convert timestamp to seconds
            amplifierTimestamps.append(rawTimestamp * timestep)

            # Expect 2 bytes of wideband data.
            rawSample, rawIndex = readUint16(rawData, rawIndex)
            
            # Scale this sample to convert to microVolts
            amplifierData.append(0.195 * (rawSample - 32768))

    
#initialization
# Declare buffer size for reading from TCP command socket
# This is the maximum number of bytes expected for 1 read. 1024 is plenty for a single text command
COMMAND_BUFFER_SIZE = 1024 # Increase if many return commands are expected
# Declare buffer size for reading from TCP waveform socket.
# This is the maximum number of bytes expected for 1 read
# There will be some TCP lag in both starting and stopping acquisition, so the exact number of data blocks may vary slightly.
# At 30 kHz with 1 channel, 1 second of wideband waveform data is 181,420 byte. See 'Calculations for accurate parsing' for more details
# To allow for some TCP lag in stopping acquisition resulting in slightly more than 1 second of data, 200000 should be a safe buffer size
WAVEFORM_BUFFER_SIZE = 200000 # Increase if channels, filter bands, or acquisition time increase
# Connect to TCP command server - default home IP address at port 5000
print('Connecting to TCP command server...')
scommand = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
scommand.connect(('127.0.0.1', 5000))
# Connect to TCP waveform server - default home IP address at port 5001
print('Connecting to TCP waveform server...')
swaveform = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
swaveform.connect(('127.0.0.1', 5001))
# Query runmode from RHX software
scommand.sendall(b'get runmode')
commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
isStopped = commandReturn == "Return: RunMode Stop"
# If controller is running, stop it
if not isStopped:
        scommand.sendall(b'set runmode stop')
        time.sleep(0.1) # Allow time for RHX software to accept this command before the next one comes

# Query sample rate from RHX software
scommand.sendall(b'get sampleratehertz')
commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
expectedReturnString = "Return: SampleRateHertz "
if commandReturn.find(expectedReturnString) == -1: # Look for "Return: SampleRateHertz N" where N is the sample rate
        raise Exception('Unable to get sample rate from server')
else:
        sampleRate = float(commandReturn[len(expectedReturnString):])

# Calculate timestep from sample rate
timestep = 1 / sampleRate


# Calculations for accurate parsing
# At 30 kHz with 1 channel, 1 second of wideband waveform data (including magic number, timestamps, and amplifier data) is 181,420 bytes
# N = (framesPerBlock * waveformBytesPerFrame + SizeOfMagicNumber) * NumBlocks where:
# framesPerBlock = 128 ; standard data block size used by Intan
# waveformBytesPerFrame = SizeOfTimestamp + SizeOfSample ; timestamp is a 4-byte (32-bit) int, and amplifier sample is a 2-byte (16-bit) unsigned int
# SizeOfMagicNumber = 4; Magic number is a 4-byte (32-bit) unsigned int
# NumBlocks = NumFrames / framesPerBlock ; At 30 kHz, 1 second of data has 30000 frames. NumBlocks must be an integer value, so round up to 235

framesPerBlock = 128
waveformBytesPerFrame = 4 + 2
waveformBytesPerBlock = framesPerBlock * waveformBytesPerFrame + 4

clearall()
        
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
    oldAmpT = amplifierTimestamps
    oldAmpD = amplifierData
    amplifierTimestamps = []
    amplifierData = []
    if showPlot&1==1:
        plt.plot(oldAmpT,oldAmpD)
        plt.title("ym="+str(extract(oldAmpD))
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (uV)')
        plt.show()
    if showPlot&2==2:
        plt.plot(range(0,len(oldAmpD)),oldAmpD)
        plt.title("ym="+str(extract(oldAmpD)))
        plt.xlabel('index')
        plt.ylabel('Voltage (uV)')
        plt.show()
    acq_thread.start()
    nxtacq_thread = threading.Thread(target=acq, daemon=True)
    ym[0] = extract(oldAmpD)
    validseq(oldAmpT)
    print("ym="+str(ym[0]))
    concore.write(1,"ym",ym)
acq_thread.join()
print("retry="+str(concore.retrycount))
