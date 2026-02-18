import time
from ast import literal_eval
import re
import os
import logging
import zmq
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

class ZeroMQPort:
    def __init__(self, port_type, address, zmq_socket_type):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq_socket_type)
        self.port_type = port_type
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
        return#avoid reinstallation
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
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, list):
        return [convert_numpy_to_python(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_python(item) for item in obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_python(value) for key, value in obj.items()}
    else:
        return obj

def safe_literal_eval(filename, defaultValue):
    try:
        with open(filename, "r") as file:
            return literal_eval(file.read())
    except (FileNotFoundError, SyntaxError, ValueError, Exception) as e:
        logging.info(f"Error reading {filename}: {e}")
        return defaultValue
    
iport = safe_literal_eval("concore.iport", {})
oport = safe_literal_eval("concore.oport", {})

s = ''
olds = ''
delay = 1
retrycount = 0
inpath = os.path.abspath("/in")
outpath = os.path.abspath("/out")
simtime = 0
concore_params_file = os.path.join(inpath + "1", "concore.params")
concore_maxtime_file = os.path.join(inpath + "1", "concore.maxtime")

#9/21/22
def parse_params(sparams):
    params = {}
    if not sparams:
        return params

    s = sparams.strip()

    # full dict literal
    if s.startswith("{") and s.endswith("}"):
        try:
            val = literal_eval(s)
            if isinstance(val, dict):
                return val
        except (ValueError, SyntaxError):
            pass

    # Potentially breaking backward compatibility: moving away from the comma-separated params
    for item in s.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            key = key.strip()
            value = value.strip()
            #try to convert to python type (int, float, list, etc.)
            # Use literal_eval to preserve backward compatibility (integers/lists)
            # Fallback to string for unquoted values (paths, URLs)
            try:
                params[key] = literal_eval(value)
            except (ValueError, SyntaxError):
                params[key] = value
    return params

try:
    with open(concore_params_file, "r") as f:
        sparams = f.read().strip()

    if sparams and sparams[0] == '"':  # windows keeps quotes
        sparams = sparams[1:]
        if '"' in sparams:
            sparams = sparams[:sparams.find('"')]

    if sparams:
        logging.debug("parsing sparams: "+sparams)
        params = parse_params(sparams)
        logging.debug("parsed params: " + str(params))
    else:
        params = dict()
except Exception as e:
    logging.error(f"Error reading concore.params: {e}")
    params = dict()

#9/30/22
def tryparam(n, i):
    return params.get(n, i)

#9/12/21
def default_maxtime(default):
    global maxtime
    maxtime = safe_literal_eval(concore_maxtime_file, default)

default_maxtime(100)

def unchanged():
    global olds, s
    if olds == s:
        s = ''
        return True
    olds = s
    return False

def read(port_identifier, name, initstr_val):
    global s, simtime, retrycount
    
    default_return_val = initstr_val
    if isinstance(initstr_val, str):
        try:
            default_return_val = literal_eval(initstr_val)
        except (SyntaxError, ValueError):
            # Failed to parse initstr_val; fall back to the original string value.
            logging.debug(
                "Could not parse initstr_val %r with literal_eval; using raw string as default.",
                initstr_val
            )
    
    if isinstance(port_identifier, str) and port_identifier in zmq_ports:
        zmq_p = zmq_ports[port_identifier]
        try:
            message = zmq_p.recv_json_with_retry()
            if isinstance(message, list) and len(message) > 0:
                first_element = message[0]
                if isinstance(first_element, (int, float)):
                    simtime = max(simtime, first_element)
                    return message[1:]
            return message
        except zmq.error.ZMQError as e:
            logging.error(f"ZMQ read error on port {port_identifier} (name: {name}): {e}. Returning default.")
            return default_return_val
        except Exception as e:
            logging.error(f"Unexpected error during ZMQ read on port {port_identifier} (name: {name}): {e}. Returning default.")
            return default_return_val

    try:
        file_port_num = int(port_identifier)
    except ValueError:
        logging.error(f"Error: Invalid port identifier '{port_identifier}' for file operation. Must be integer or ZMQ name.")
        return default_return_val

    time.sleep(delay)
    # Construct file path consistent with other components (e.g., /in1/<name>)
    file_path = os.path.join(inpath, str(file_port_num), name)

    try:
        with open(file_path, "r") as infile:
            ins = infile.read()
    except FileNotFoundError:
        ins = str(initstr_val)
        s += ins
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}. Using default value.")
        return default_return_val

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
    global simtime
    
    if isinstance(port_identifier, str) and port_identifier in zmq_ports:
        zmq_p = zmq_ports[port_identifier]
        try:
            zmq_val = convert_numpy_to_python(val)
            if isinstance(zmq_val, list):
                # Prepend simtime to match file-based write behavior
                payload = [simtime + delta] + zmq_val
                zmq_p.send_json_with_retry(payload)
                simtime += delta
            else:
                zmq_p.send_json_with_retry(zmq_val)
        except zmq.error.ZMQError as e:
            logging.error(f"ZMQ write error on port {port_identifier} (name: {name}): {e}")
        except Exception as e:
            logging.error(f"Unexpected error during ZMQ write on port {port_identifier} (name: {name}): {e}")
        return

    try:
        file_port_num = int(port_identifier)
        file_path = os.path.join(outpath, str(file_port_num), name)
    except ValueError:
        logging.error(f"Error: Invalid port identifier '{port_identifier}' for file operation. Must be integer or ZMQ name.")
        return

    if isinstance(val, str):
        time.sleep(2 * delay)
    elif not isinstance(val, list):
        logging.error(f"File write to {file_path} must have list or str value, got {type(val)}")
        return

    try:
        with open(file_path, "w") as outfile:
            if isinstance(val, list):
                val_converted = convert_numpy_to_python(val)
                data_to_write = [simtime + delta] + val_converted
                outfile.write(str(data_to_write))
                simtime += delta
            else:
                outfile.write(val)
    except Exception as e:
        logging.error(f"Error writing to {file_path}: {e}")

def initval(simtime_val):
    global simtime
    try:
        val = literal_eval(simtime_val)
        if isinstance(val, list) and len(val) > 0:
            first_element = val[0]
            if isinstance(first_element, (int, float)):
                simtime = first_element
                return val[1:]
            else:
                logging.error(f"Error: First element in initval string '{simtime_val}' is not a number. Using data part as is or empty.")
                return val[1:] if len(val) > 1 else []
        else:
            logging.error(f"Error: initval string '{simtime_val}' is not a list or is empty. Returning empty list.")
            return []
    except Exception as e:
        logging.error(f"Error parsing simtime_val_str '{simtime_val}': {e}. Returning empty list.")
        return []

