import time
import logging
import os
from ast import literal_eval
import sys
import re
import zmq
import numpy as np
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
) # Added for ZeroMQ

# if windows, create script to kill this process 
# because batch files don't provide easy way to know pid of last command
# ignored for posix != windows, because "concorepid" is handled by script
# ignored for docker (linux != windows), because handled by docker stop
if hasattr(sys, 'getwindowsversion'):
    with open("concorekill.bat","w") as fpid:
        fpid.write("taskkill /F /PID "+str(os.getpid())+"\n")

# ===================================================================
# ZeroMQ Communication Wrapper
# ===================================================================
class ZeroMQPort:
    def __init__(self, port_type, address, zmq_socket_type):
        """
        port_type: "bind" or "connect"
        address: ZeroMQ address (e.g., "tcp://*:5555")
        zmq_socket_type: zmq.REQ, zmq.REP, zmq.PUB, zmq.SUB etc.
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq_socket_type)
        self.port_type = port_type  # "bind" or "connect"
        self.address = address

        # Configure timeouts & immediate close on failure
        self.socket.setsockopt(zmq.RCVTIMEO, 2000)   # 2 sec receive timeout
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)   # 2 sec send timeout
        self.socket.setsockopt(zmq.LINGER, 0)        # Drop pending messages on close

        # Bind or connect
        if self.port_type == "bind":
            self.socket.bind(address)
            logging.info(f"ZMQ Port bound to {address}")
        else:
            self.socket.connect(address)
            logging.info(f"ZMQ Port connected to {address}")
            
    def send_json_with_retry(self, message):
        """Send JSON message with retries if timeout occurs."""
        for attempt in range(5):
            try:
                self.socket.send_json(message)
                return
            except zmq.Again:
                logging.warning(f"Send timeout (attempt {attempt + 1}/5)")
                time.sleep(0.5)
        logging.error("Failed to send after retries.")
        return

    def recv_json_with_retry(self):
        """Receive JSON message with retries if timeout occurs."""
        for attempt in range(5):
            try:
                return self.socket.recv_json()
            except zmq.Again:
                logging.warning(f"Receive timeout (attempt {attempt + 1}/5)")
                time.sleep(0.5)
        logging.error("Failed to receive after retries.")
        return None

# Global ZeroMQ ports registry
zmq_ports = {}

def init_zmq_port(port_name, port_type, address, socket_type_str):
    """
    Initializes and registers a ZeroMQ port.
    port_name (str): A unique name for this ZMQ port.
    port_type (str): "bind" or "connect".
    address (str): The ZMQ address (e.g., "tcp://*:5555", "tcp://localhost:5555").
    socket_type_str (str): String representation of ZMQ socket type (e.g., "REQ", "REP", "PUB", "SUB").
    """
    if port_name in zmq_ports:
        logging.info(f"ZMQ Port {port_name} already initialized.")
        return # Avoid reinitialization
    
    try:
        # Map socket type string to actual ZMQ constant (e.g., zmq.REQ, zmq.REP)
        zmq_socket_type = getattr(zmq, socket_type_str.upper())
        zmq_ports[port_name] = ZeroMQPort(port_type, address, zmq_socket_type)
        logging.info(f"Initialized ZMQ port: {port_name} ({socket_type_str}) on {address}")
    except AttributeError:
        logging.error(f"Error: Invalid ZMQ socket type string '{socket_type_str}'.")
    except zmq.error.ZMQError as e:
        logging.error(f"Error initializing ZMQ port {port_name} on {address}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during ZMQ port initialization for {port_name}: {e}")

def terminate_zmq():
    for port in zmq_ports.values():
        try:
            port.socket.close()
            port.context.term()
        except Exception as e:
            logging.error(f"Error while terminating ZMQ port {port.address}: {e}")
# --- ZeroMQ Integration End ---


# NumPy Type Conversion Helper
def convert_numpy_to_python(obj):
    #Recursively convert numpy types to native Python types.
    #This is necessary because literal_eval cannot parse numpy representations
    #like np.float64(1.0), but can parse native Python types like 1.0.
    if isinstance(obj, np.generic):
        # Convert numpy scalar types to Python native types
        return obj.item()
    elif isinstance(obj, list):
        return [convert_numpy_to_python(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_python(item) for item in obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_python(value) for key, value in obj.items()}
    else:
        return obj

# ===================================================================
# File & Parameter Handling
# ===================================================================
def safe_literal_eval(filename, defaultValue):
    try:
        with open(filename, "r") as file:
            return literal_eval(file.read())
    except (FileNotFoundError, SyntaxError, ValueError, Exception) as e:
        # Keep print for debugging, but can be made quieter
        # print(f"Info: Error reading {filename} or file not found, using default: {e}")
        return defaultValue


# Load input/output ports if present
iport = safe_literal_eval("concore.iport", {})
oport = safe_literal_eval("concore.oport", {})

# Global variables
s = ''
olds = ''
delay = 1
retrycount = 0
inpath = "./in" #must be rel path for local
outpath = "./out"
simtime = 0
concore_params_file = os.path.join(inpath + "1", "concore.params")
concore_maxtime_file = os.path.join(inpath + "1", "concore.maxtime")

#9/21/22
# ===================================================================
# Parameter Parsing
# ===================================================================
try:
    sparams_path = concore_params_file
    if os.path.exists(sparams_path):
        with open(sparams_path, "r") as f:
            sparams = f.read()
        if sparams: # Ensure sparams is not empty
            # Windows sometimes keeps quotes
            if sparams[0] == '"' and sparams[-1] == '"':  #windows keeps "" need to remove
                sparams = sparams[1:-1]

            # Convert key=value;key2=value2 to Python dict format
            if sparams != '{' and not (sparams.startswith('{') and sparams.endswith('}')): # Check if it needs conversion
                logging.debug("converting sparams: "+sparams)
                sparams = "{'"+re.sub(';',",'",re.sub('=',"':",re.sub(' ','',sparams)))+"}"
                logging.debug("converted sparams: " + sparams)
            try:
                params = literal_eval(sparams)
            except Exception as e:
                logging.warning(f"bad params content: {sparams}, error: {e}")
                params = dict()
        else:
            params = dict()
    else:
        params = dict()
except Exception as e:
    # print(f"Info: concore.params not found or error reading, using empty dict: {e}")
    params = dict()

#9/30/22
def tryparam(n, i):
    """Return parameter `n` from params dict, else default `i`."""
    return params.get(n, i)


#9/12/21
# ===================================================================
# Simulation Time Handling
# ===================================================================
def default_maxtime(default):
    """Read maximum simulation time from file or use default."""
    global maxtime
    maxtime = safe_literal_eval(concore_maxtime_file, default)

default_maxtime(100)

def unchanged():
    """Check if global string `s` is unchanged since last call."""
    global olds, s
    if olds == s:
        s = ''
        return True
    olds = s
    return False

# ===================================================================
# I/O Handling (File + ZMQ)
# ===================================================================
def read(port_identifier, name, initstr_val):
    global s, simtime, retrycount
    
    # Default return
    default_return_val = initstr_val
    if isinstance(initstr_val, str):
        try:
            default_return_val = literal_eval(initstr_val)
        except (SyntaxError, ValueError):
            pass
    
    # Case 1: ZMQ port
    if isinstance(port_identifier, str) and port_identifier in zmq_ports:
        zmq_p = zmq_ports[port_identifier]
        try:
            message = zmq_p.recv_json_with_retry()
            return message
        except zmq.error.ZMQError as e:
            logging.error(f"ZMQ read error on port {port_identifier} (name: {name}): {e}. Returning default.")
            return default_return_val
        except Exception as e:
            logging.error(f"Unexpected error during ZMQ read on port {port_identifier} (name: {name}): {e}. Returning default.")
            return default_return_val

    # Case 2: File-based port
    try:
        file_port_num = int(port_identifier)
    except ValueError:
        logging.error(f"Error: Invalid port identifier '{port_identifier}' for file operation. Must be integer or ZMQ name.")
        return default_return_val

    time.sleep(delay) 
    file_path = os.path.join(inpath + str(file_port_num), name)
    ins = ""

    try:
        with open(file_path, "r") as infile:
            ins = infile.read()
    except FileNotFoundError:
        ins = str(initstr_val) 
        s += ins  # Update s to break unchanged() loop
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}. Using default value.")
        return default_return_val 

    # Retry logic if file is empty
    attempts = 0
    max_retries = 5 
    while len(ins) == 0 and attempts < max_retries:
        time.sleep(delay)
        try:
            with open(file_path, "r") as infile:
                ins = infile.read()
        except Exception as e:
            logging.warning(f"Retry {attempts + 1}: Error reading {file_path} - {e}")
        attempts += 1
        retrycount += 1

    if len(ins) == 0:
        logging.error(f"Max retries reached for {file_path}, using default value.")
        return default_return_val

    s += ins 

    # Try parsing
    try:
        inval = literal_eval(ins)
        if isinstance(inval, list) and len(inval) > 0: 
            current_simtime_from_file = inval[0]
            if isinstance(current_simtime_from_file, (int, float)):
                 simtime = max(simtime, current_simtime_from_file)
            return inval[1:] 
        else: 
            logging.warning(f"Warning: Unexpected data format in {file_path}: {ins}. Returning raw content or default.")
            return inval 
    except Exception as e:
        logging.error(f"Error parsing content from {file_path} ('{ins}'): {e}. Returning default.")
        return default_return_val


def write(port_identifier, name, val, delta=0):
    """
    Write data either to ZMQ port or file.
    `val` must be list (with simtime prefix) or string.
    """
    global simtime

    # Case 1: ZMQ port
    if isinstance(port_identifier, str) and port_identifier in zmq_ports:
        zmq_p = zmq_ports[port_identifier]
        try:
            zmq_p.send_json_with_retry(val)
        except zmq.error.ZMQError as e:
            logging.error(f"ZMQ write error on port {port_identifier} (name: {name}): {e}")
        except Exception as e:
            logging.error(f"Unexpected error during ZMQ write on port {port_identifier} (name: {name}): {e}")
    
    # Case 2: File-based port
    try:
        file_port_num = int(port_identifier)
        file_path = os.path.join(outpath + str(file_port_num), name) 
    except ValueError:
        logging.error(f"Error: Invalid port identifier '{port_identifier}' for file operation. Must be integer or ZMQ name.")
        return

    # File writing rules
    if isinstance(val, str):
        time.sleep(2 * delay) # string writes wait longer
    elif not isinstance(val, list):
        logging.error(f"File write to {file_path} must have list or str value, got {type(val)}")
        return

    try:
        with open(file_path, "w") as outfile:
            if isinstance(val, list):
                # Convert numpy types to native Python types
                val_converted = convert_numpy_to_python(val)
                data_to_write = [simtime + delta] + val_converted
                outfile.write(str(data_to_write))
                simtime += delta 
            else: 
                outfile.write(val)
    except Exception as e:
        logging.error(f"Error writing to {file_path}: {e}")

def initval(simtime_val_str): 
    """
    Initialize simtime from string containing a list.
    Example: "[10, 'foo', 'bar']" → simtime=10, returns ['foo','bar']
    """
    global simtime
    try:
        val = literal_eval(simtime_val_str)
        if isinstance(val, list) and len(val) > 0:
            first_element = val[0]
            if isinstance(first_element, (int, float)):
                simtime = first_element
                return val[1:] 
            else:
                logging.error(f"Error: First element in initval string '{simtime_val_str}' is not a number. Using data part as is or empty.")
                return val[1:] if len(val) > 1 else [] 
        else: 
            logging.error(f"Error: initval string '{simtime_val_str}' is not a list or is empty. Returning empty list.")
            return []

    except Exception as e:
        logging.error(f"Error parsing simtime_val_str '{simtime_val_str}': {e}. Returning empty list.")
        return []