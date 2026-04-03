# funbody2_zmq.py
import time 
import concore

print("funbody using ZMQ via concore")

# Initialize ZMQ REP port using concore
concore.init_zmq_port(
    port_name=PORT_NAME_F2_F1,
    port_type="bind",
    address= "tcp://*:" + PORT_F2_F1,
    socket_type_str="REP" 
)

# Standard concore initializations
concore.delay = 0.07         
concore.simtime = 0         
concore.default_maxtime(100) 
init_simtime_u_str = "[0.0, 0.0, 0.0]"
init_simtime_ym_str = "[0.0, 0.0, 0.0]"

u_data_values = concore.initval(init_simtime_u_str) 
ym_data_values = concore.initval(init_simtime_ym_str)

print(f"Initial u_data_values: {u_data_values}, ym_data_values: {ym_data_values}")
print(f"Max time: {concore.maxtime}")

while concore.simtime < concore.maxtime:
    received_u_data = concore.read(PORT_NAME_F2_F1, "u_signal", init_simtime_u_str)

    if not (isinstance(received_u_data, list) and len(received_u_data) > 0):
        print(f"Error or invalid data received via ZMQ: {received_u_data}. Skipping iteration.")
        time.sleep(concore.delay) 
        continue 

    received_time = received_u_data[0]
    if isinstance(received_time, (int, float)):
        concore.simtime = received_time  
        u_data_values = received_u_data[1:] 
    else:
        print(f"Warning: Received ZMQ data's first element is not time: {received_u_data}. Using data part as is.")
        u_data_values = received_u_data[1:] if len(received_u_data) > 1 else []

    # Assuming concore.oport['U2'] is a file port (e.g., to pmpymax.py)
    if 'U2' in concore.oport: 
        concore.write(concore.oport['U2'], "u", u_data_values)

    # Take a numeric snapshot of the current simulation time to avoid
    # inadvertently sharing a reference with concore.simtime.
    old_concore_simtime = float(concore.simtime)
    while concore.unchanged() or concore.simtime <= old_concore_simtime:
        # Assuming concore.iport['Y2'] is a file port (e.g., from pmpymax.py)
        ym_data_values = concore.read(concore.iport['Y2'], "ym", init_simtime_ym_str)
        # time.sleep(concore.delay) # Optional delay

    ym_full_to_send = [concore.simtime] + ym_data_values
    
    concore.write(PORT_NAME_F2_F1, "ym_signal", ym_full_to_send)
    
    print(f"funbody u={u_data_values} ym={ym_data_values} time={concore.simtime}")

print("funbody retry=" + str(concore.retrycount))

concore.terminate_zmq()