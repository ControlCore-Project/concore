# A.py (Client and Primary Measurement Node)
import concore
import time
import os
import psutil
import sys

# --- Fallback Definitions for Direct Execution ---
# These values are normally injected by copy_with_port_portname.py during study generation.
# When running this script directly, safe defaults are used instead.
_STANDALONE_MODE = False

if 'PORT_NAME_F1_F2' not in globals():
    PORT_NAME_F1_F2 = "F1_F2"
    _STANDALONE_MODE = True

if 'PORT_F1_F2' not in globals():
    PORT_F1_F2 = "5555"
    _STANDALONE_MODE = True

if _STANDALONE_MODE:
    print("Warning: Port variables not injected. Running in standalone mode with default values.")
    print("         For full study behavior, run via study generation (makestudy).")

# --- ZMQ Initialization ---
# This REQ socket connects to Node B
concore.init_zmq_port(
    port_name=PORT_NAME_F1_F2,
    port_type="connect",
    address="tcp://localhost:" + PORT_F1_F2,
    socket_type_str="REQ"
)

print("Node A client started.")

# --- Measurement Initialization ---
min_latency = float('inf')
max_latency = 0.0
total_latency = 0.0
message_count = 0
total_bytes = 0
process = psutil.Process(os.getpid())
overall_start_time = time.monotonic()
loop_start_time = 0

current_value = 0
max_value = 100

while current_value < max_value:
    loop_start_time = time.monotonic() # Start timer for round-trip latency
    print(f"Node A: Sending value {current_value:.2f} to Node B.")
    
    # 1. Send the current value as a request to the pipeline
    concore.write(PORT_NAME_F1_F2, "value", [current_value])
    total_bytes += sys.getsizeof([current_value])

    # 2. Wait for the final, processed value in reply
    received_data = concore.read(PORT_NAME_F1_F2, "value", [0.0])
    
    loop_end_time = time.monotonic()
    latency_ms = (loop_end_time - loop_start_time) * 1000

    # Update metrics
    message_count += 1
    min_latency = min(min_latency, latency_ms)
    max_latency = max(max_latency, latency_ms)
    total_latency += latency_ms

    current_value = received_data[0]
    print(f"Node A: Received final value {current_value:.2f} from the pipeline. | Latency: {latency_ms:.2f} ms")
    print("-" * 20)

# --- Finalize and Report Measurements ---
overall_end_time = time.monotonic()
total_duration = overall_end_time - overall_start_time
cpu_usage = process.cpu_percent() / total_duration if total_duration > 0 else 0
avg_latency = total_latency / message_count if message_count > 0 else 0

print("\n" + "="*35)
print("--- NODE A: END-TO-END RESULTS ---")
print(f"Total pipeline iterations: {message_count}")
print(f"Total data sent:           {total_bytes / 1024:.4f} KB")
print(f"Total End-to-End Time:     {total_duration:.4f} seconds")
print("-" * 35)
print(f"Min round-trip latency:    {min_latency:.2f} ms")
print(f"Avg round-trip latency:    {avg_latency:.2f} ms")
print(f"Max round-trip latency:    {max_latency:.2f} ms")
print("-" * 35)
print(f"Approximate CPU usage:     {cpu_usage:.2f}%")
print("="*35)

print(f"\nNode A: Final value {current_value:.2f} reached the target. Terminating.")
concore.terminate_zmq()
