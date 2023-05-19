# Start IntanRHX in one window

````
$ Downloads/IntanRHX/IntanRHX
````

In order to run this example script successfully, the Intan RHX software should first be started, and through Network -> Remote TCP Control:

Command Output should open a connection at 127.0.0.1, Port 5000. Status should read "Pending"

Waveform Output (in the Data Output tab) should open a connection at 127.0.0.1, Port 5001.
Status should read "Pending" for the Waveform Port (Spike Port is unused for this example, and can be left disconnected)

# Run RHXReadWaveformData.py in another window

This will eventually be replaced by the step to start _concore._

````
$ cd ~/concore/
$ python3 RHXReadWaveformData.py
````
