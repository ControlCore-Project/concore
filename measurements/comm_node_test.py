import concore
import time
import sys

# --- Script Configuration ---
concore.delay = 0.07
concore.simtime = 0
concore.default_maxtime(100) # This will be ignored by the new logic
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

# --- Measurement Initialization ---
messages_processed = 0
start_time = time.monotonic()

# --- Main Script Logic ---
u = concore.initval(init_simtime_u)
ym = concore.initval(init_simtime_ym)
curr = 0
max_value = 100
iteration = 0
iteration_limit = 15 # Safety break

print("comm_node_test.py started...")

while curr < max_value and iteration < iteration_limit:
    # 1. Wait for a message from the 'u' channel
    while concore.unchanged():
        u = concore.read(concore.iport['U'], "u", init_simtime_u)
    
    # 2. Forward it to the 'U1' channel
    concore.write(concore.oport['U1'], "u", u)
    curr = u[0]
    
    # Break if the loop condition is met after the first read
    if curr >= max_value:
        # Forward a final message to ensure the next node also terminates
        concore.write(concore.oport['Y'], "ym", [curr])
        break

    # 3. Wait for a message from the 'Y1' channel
    old2 = float(concore.simtime)
    while concore.unchanged() or concore.simtime <= old2:
        ym = concore.read(concore.iport['Y1'], "ym", init_simtime_ym)
        
    # 4. Forward it to the 'Y' channel
    concore.write(concore.oport['Y'], "ym", ym)
    curr = ym[0]
    
    print(f"comm_node: u={u[0]:.2f} | ym={ym[0]:.2f}")
    
    messages_processed += 2 # Counting one read and one write as two "processed" messages
    iteration += 1

# --- Finalize and Report Measurements ---
end_time = time.monotonic()
duration = end_time - start_time

print("\n" + "="*30)
print("--- COMM_NODE_TEST: FINAL RESULTS ---")
print(f"Total messages routed: {messages_processed}")
print(f"Total execution time:  {duration:.4f} seconds")
print(f"concore retry count:   {concore.retrycount}")
print("="*30)
