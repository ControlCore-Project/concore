# funcall_distributed.py (MODIFIED FOR LATENCY MEASUREMENT)
import time
import concore
import csv # <--- ADDED: Import CSV library

print("funcall using ZMQ via concore")

# This assumes PORT_NAME_IN_F1, PORT_IN_F1 are defined elsewhere before this script runs
concore.init_zmq_port(
    port_name=PORT_NAME_IN_F1,
    port_type="connect",
    address="tcp://192.168.0.109:" + PORT_IN_F1, # The IP address of the machine running funbody
    socket_type_str="REQ"
)

# Standard concore initializations
concore.delay = 0.07
concore.simtime = 0
concore.default_maxtime(100) # Recommend increasing this for more data points, e.g., 1000
init_simtime_u_str = "[0.0, 0.0, 0.0]"
init_simtime_ym_str = "[0.0, 0.0, 0.0]"

u = concore.initval(init_simtime_u_str)
ym = concore.initval(init_simtime_ym_str)

# --- ADDED: Initialize a list to store latency values ---
zeromq_latencies = []

print(f"Initial u: {u}, ym: {ym}, concore.simtime: {concore.simtime}, concore.simtime: {concore.simtime}")
print(f"Max time: {concore.maxtime}")

while concore.simtime < concore.maxtime:
    while concore.unchanged():
        u = concore.read(concore.iport['U'], "u", init_simtime_u_str)

    data_to_send_u = [concore.simtime] + u
    
    # --- MODIFIED: Add timing logic around the ZMQ communication ---
    start_time = time.perf_counter()
    
    concore.write(PORT_NAME_IN_F1, "u_signal", data_to_send_u)
    received_ym_data = concore.read(PORT_NAME_IN_F1, "ym_signal", init_simtime_ym_str)
    
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    zeromq_latencies.append(latency_ms)
    # --- END OF MODIFICATION ---

    if isinstance(received_ym_data, list) and len(received_ym_data) > 0:
        response_time = received_ym_data[0]
        if isinstance(response_time, (int, float)):
            concore.simtime = response_time
            ym = received_ym_data[1:]
        else:
            print(f"Warning: Received ZMQ data's first element is not time: {received_ym_data}. Using as is.")
            ym = received_ym_data
    else:
        print(f"Warning: Received unexpected ZMQ data format: {received_ym_data}. Using default ym.")
        ym = concore.initval(init_simtime_ym_str)

    concore.write(concore.oport['Y'], "ym", ym)
    
    print(f"funcall ZMQ u={u} ym={ym} time={concore.simtime} | ZMQ Latency: {latency_ms:.4f} ms")

print("funcall retry=" + str(concore.retrycount))

# --- ADDED: Save the collected latencies to a CSV file ---
# Discard the first few values as a "warm-up"
warmup_period = 5
if len(zeromq_latencies) > warmup_period:
    with open('zeromq_latencies.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Latency (ms)'])
        for latency in zeromq_latencies[warmup_period:]:
            writer.writerow([latency])
    print("Latency data saved to zeromq_latencies.csv")
# --- END OF ADDITION ---

concore.terminate_zmq()