# C.py (Processing Server and Measurement Endpoint)
import concore
import time
import psutil
import os
import sys

# --- Fallback Definitions for Direct Execution ---
# These values are normally injected by copy_with_port_portname.py during study generation.
# When running this script directly, safe defaults are used instead.
_STANDALONE_MODE = False

if 'PORT_NAME_F2_F3' not in globals():
    PORT_NAME_F2_F3 = "F2_F3"
    _STANDALONE_MODE = True

if 'PORT_F2_F3' not in globals():
    PORT_F2_F3 = "5556"
    _STANDALONE_MODE = True

if _STANDALONE_MODE:
    print("Warning: Port variables not injected. Running in standalone mode with default values.")
    print("         For full study behavior, run via study generation (makestudy).")

# --- ZMQ Initialization ---
# This REP socket binds and waits for requests from Node B
concore.init_zmq_port(
    port_name=PORT_NAME_F2_F3,
    port_type="bind",
    address="tcp://*:" + PORT_F2_F3,
    socket_type_str="REP"
)

print("Node C server started. Waiting for requests...")

# --- Measurement Initialization ---
process = psutil.Process(os.getpid())
start_time = time.monotonic()
message_count = 0
total_bytes = 0

while True:
    # 1. Wait to receive a request from Node B
    received_data = concore.read(PORT_NAME_F2_F3, "value", [0.0])
    received_value = received_data[0]
    
    # Track received data for metrics
    message_count += 1
    total_bytes += sys.getsizeof(received_data)
    
    print(f"Node C: Received {received_value:.2f} from Node B.")

    # 2. Process the value (increment by 10)
    new_value = received_value + 10
    print(f"Node C: Sending back processed value {new_value:.2f}.")

    # 3. Send the reply back to Node B
    concore.write(PORT_NAME_F2_F3, "value", [new_value])
    
    # 4. Check the value to know when to shut down gracefully.
    if new_value >= 100:
        break

# --- Finalize and Report Measurements ---
end_time = time.monotonic()
duration = end_time - start_time
# This captures the CPU usage over the process's lifetime relative to the test duration
cpu_usage = process.cpu_percent() / duration if duration > 0 else 0

print("\n" + "="*30)
print("--- NODE C: RESULTS ---")
print(f"Total messages processed: {message_count}")
print(f"Total data processed:     {total_bytes / 1024:.4f} KB")
print(f"Total execution time:     {duration:.4f} seconds")
print(f"Approximate CPU usage:    {cpu_usage:.2f}%")
print("="*30)

print("\nNode C: Terminating.")
concore.terminate_zmq()
