import time
import logging
import os
from ast import literal_eval
import zmq
import numpy as np

logger = logging.getLogger('concore')
logger.addHandler(logging.NullHandler())

# ===================================================================
# ZeroMQ Communication Wrapper
# ===================================================================
# lazy-initialized shared ZMQ context for the entire process.
# using None until first ZMQ port is created, so file-only workflows
# never spawn ZMQ I/O threads at import time.
_zmq_context = None

def _get_zmq_context():
    """Return the process-level shared ZMQ context, creating it on first call."""
    global _zmq_context
    if _zmq_context is None or _zmq_context.closed:
        _zmq_context = zmq.Context()
    return _zmq_context

class ZeroMQPort:
    def __init__(self, port_type, address, zmq_socket_type, context=None):
        """
        port_type: "bind" or "connect"
        address: ZeroMQ address (e.g., "tcp://*:5555")
        zmq_socket_type: zmq.REQ, zmq.REP, zmq.PUB, zmq.SUB etc.
        context: optional zmq.Context() for the process; defaults to the shared _zmq_context.
        """
        if context is None:
            context = _get_zmq_context()
        self.socket = context.socket(zmq_socket_type)
        self.port_type = port_type  # "bind" or "connect"
        self.address = address

        # Configure timeouts & immediate close on failure
        self.socket.setsockopt(zmq.RCVTIMEO, 2000)   # 2 sec receive timeout
        self.socket.setsockopt(zmq.SNDTIMEO, 2000)   # 2 sec send timeout
        self.socket.setsockopt(zmq.LINGER, 0)        # Drop pending messages on close

        # Bind or connect
        if self.port_type == "bind":
            self.socket.bind(address)
            logger.info(f"ZMQ Port bound to {address}")
        else:
            self.socket.connect(address)
            logger.info(f"ZMQ Port connected to {address}")
            
    def send_json_with_retry(self, message):
        """Send JSON message with retries if timeout occurs."""
        for attempt in range(5):
            try:
                self.socket.send_json(message)
                return
            except zmq.Again:
                logger.warning(f"Send timeout (attempt {attempt + 1}/5)")
                time.sleep(0.5)
        logger.error("Failed to send after retries.")
        return

    def recv_json_with_retry(self):
        """Receive JSON message with retries if timeout occurs."""
        for attempt in range(5):
            try:
                return self.socket.recv_json()
            except zmq.Again:
                logger.warning(f"Receive timeout (attempt {attempt + 1}/5)")
                time.sleep(0.5)
        logger.error("Failed to receive after retries.")
        return None


def init_zmq_port(mod, port_name, port_type, address, socket_type_str):
    """
    Initializes and registers a ZeroMQ port.
    mod: calling module (has zmq_ports dict)
    port_name (str): A unique name for this ZMQ port.
    port_type (str): "bind" or "connect".
    address (str): The ZMQ address (e.g., "tcp://*:5555", "tcp://localhost:5555").
    socket_type_str (str): String representation of ZMQ socket type (e.g., "REQ", "REP", "PUB", "SUB").
    """
    if port_name in mod.zmq_ports:
        logger.info(f"ZMQ Port {port_name} already initialized.")
        return # Avoid reinitialization
    
    try:
        # Map socket type string to actual ZMQ constant (e.g., zmq.REQ, zmq.REP)
        zmq_socket_type = getattr(zmq, socket_type_str.upper())
        mod.zmq_ports[port_name] = ZeroMQPort(port_type, address, zmq_socket_type, _get_zmq_context())
        logger.info(f"Initialized ZMQ port: {port_name} ({socket_type_str}) on {address}")
    except AttributeError:
        logger.error(f"Error: Invalid ZMQ socket type string '{socket_type_str}'.")
    except zmq.error.ZMQError as e:
        logger.error(f"Error initializing ZMQ port {port_name} on {address}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during ZMQ port initialization for {port_name}: {e}")

def terminate_zmq(mod):
    """Clean up all ZMQ sockets, then terminate the shared context once."""
    global _zmq_context  # declared first — used both in the early-return guard and reset below
    if mod._cleanup_in_progress:
        return  # Already cleaning up, prevent reentrant calls

    if not mod.zmq_ports and (_zmq_context is None or _zmq_context.closed):
        return  # Nothing to clean up: no ports and no active context

    mod._cleanup_in_progress = True
    print("\nCleaning up ZMQ resources...")

    # all sockets must be closed before context.term() is called.
    for port_name, port in mod.zmq_ports.items():
        try:
            port.socket.close()
            print(f"Closed ZMQ port: {port_name}")
        except Exception as e:
            logger.error(f"Error while terminating ZMQ port {port.address}: {e}")
    mod.zmq_ports.clear()

    # terminate the single shared context exactly once, then reset so it
    # can be safely recreated if init_zmq_port is called again later.
    if _zmq_context is not None and not _zmq_context.closed:
        try:
            _zmq_context.term()
        except Exception as e:
            logger.error(f"Error while terminating shared ZMQ context: {e}")
        _zmq_context = None

    mod._cleanup_in_progress = False

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
        # print(f"Info: Error reading {filename} or file not found, using default: {e}")
        return defaultValue

#9/21/22
# ===================================================================
# Parameter Parsing
# ===================================================================
def parse_params(sparams):
    params = {}
    if not sparams:
        return params

    s = sparams.strip()

    #full dict literal
    if s.startswith("{") and s.endswith("}"):
        try:
            val = literal_eval(s)
            if isinstance(val, dict):
                return val
        except (ValueError, SyntaxError):
            pass

    for item in s.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)  # split only once
            key=key.strip()
            value=value.strip()
            #try to convert to python type (int, float, list, etc.)
            # Use literal_eval to preserve backward compatibility (integers/lists)
            # Fallback to string for unquoted values (paths, URLs)
            try:
                params[key] = literal_eval(value)
            except (ValueError, SyntaxError):
                params[key] = value
    return params

def load_params(params_file):
    try:
        if os.path.exists(params_file):
            with open(params_file, "r") as f:
                sparams = f.read().strip()
            if sparams:
                # Windows sometimes keeps quotes
                if sparams[0] == '"' and sparams[-1] == '"':  #windows keeps "" need to remove
                    sparams = sparams[1:-1]
                logger.debug("parsing sparams: "+sparams)
                p = parse_params(sparams)
                logger.debug("parsed params: " + str(p))
                return p
        return dict()
    except Exception:
        return dict()

# ===================================================================
# Read Status Tracking
# ===================================================================
last_read_status = "SUCCESS"

# ===================================================================
# I/O Handling (File + ZMQ)
# ===================================================================

def unchanged(mod):
    """Check if global string `s` is unchanged since last call."""
    if mod.olds == mod.s:
        mod.s = ''
        return True
    mod.olds = mod.s
    return False


def read(mod, port_identifier, name, initstr_val):
    """Read data from a ZMQ port or file-based port.

    Returns:
        tuple: (data, success_flag) where success_flag is True if real
            data was received, False if a fallback/default was used.
            Also sets ``concore.last_read_status`` (and
            ``concore_base.last_read_status``) to one of:
            SUCCESS, FILE_NOT_FOUND, TIMEOUT, PARSE_ERROR,
            EMPTY_DATA, RETRIES_EXCEEDED.

    Backward compatibility:
        Legacy callers that do ``value = concore.read(...)`` will
        receive a tuple.  They can adapt with::

            result = concore.read(...)
            if isinstance(result, tuple):
                value, ok = result
            else:
                value, ok = result, True

        Alternatively, check ``concore.last_read_status`` after the
        call.
    """
    global last_read_status

    # Default return
    default_return_val = initstr_val
    if isinstance(initstr_val, str):
        try:
            default_return_val = literal_eval(initstr_val)
        except (SyntaxError, ValueError):
            pass
    
    # Case 1: ZMQ port
    if isinstance(port_identifier, str) and port_identifier in mod.zmq_ports:
        zmq_p = mod.zmq_ports[port_identifier]
        try:
            message = zmq_p.recv_json_with_retry()
            if message is None:
                last_read_status = "TIMEOUT"
                return default_return_val, False
            # Strip simtime prefix if present (mirroring file-based read behavior)
            if isinstance(message, list) and len(message) > 0:
                first_element = message[0]
                if isinstance(first_element, (int, float)):
                    mod.simtime = max(mod.simtime, first_element)
                    last_read_status = "SUCCESS"
                    return message[1:], True
            last_read_status = "SUCCESS"
            return message, True
        except zmq.error.ZMQError as e:
            logger.error(f"ZMQ read error on port {port_identifier} (name: {name}): {e}. Returning default.")
            last_read_status = "TIMEOUT"
            return default_return_val, False
        except Exception as e:
            logger.error(f"Unexpected error during ZMQ read on port {port_identifier} (name: {name}): {e}. Returning default.")
            last_read_status = "PARSE_ERROR"
            return default_return_val, False

    # Case 2: File-based port
    try:
        file_port_num = int(port_identifier)
    except ValueError:
        logger.error(f"Error: Invalid port identifier '{port_identifier}' for file operation. Must be integer or ZMQ name.")
        last_read_status = "PARSE_ERROR"
        return default_return_val, False

    time.sleep(mod.delay) 
    port_dir = mod._port_path(mod.inpath, file_port_num)
    file_path = os.path.join(port_dir, name)
    ins = ""

    file_not_found = False
    try:
        with open(file_path, "r") as infile:
            ins = infile.read()
    except FileNotFoundError:
        file_not_found = True
        ins = str(initstr_val) 
        mod.s += ins  # Update s to break unchanged() loop
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}. Using default value.")
        last_read_status = "FILE_NOT_FOUND"
        return default_return_val, False

    # Retry logic if file is empty
    attempts = 0
    max_retries = 5 
    while len(ins) == 0 and attempts < max_retries:
        time.sleep(mod.delay)
        try:
            with open(file_path, "r") as infile:
                ins = infile.read()
        except Exception as e:
            logger.warning(f"Retry {attempts + 1}: Error reading {file_path} - {e}")
        attempts += 1
        mod.retrycount += 1

    if len(ins) == 0:
        logger.error(f"Max retries reached for {file_path}, using default value.")
        last_read_status = "RETRIES_EXCEEDED"
        return default_return_val, False

    mod.s += ins 

    # Try parsing
    try:
        inval = literal_eval(ins)
        if isinstance(inval, list) and len(inval) > 0: 
            current_simtime_from_file = inval[0]
            if isinstance(current_simtime_from_file, (int, float)):
                 mod.simtime = max(mod.simtime, current_simtime_from_file)
            if file_not_found:
                last_read_status = "FILE_NOT_FOUND"
                return inval[1:], False
            last_read_status = "SUCCESS"
            return inval[1:], True
        else: 
            logger.warning(f"Warning: Unexpected data format in {file_path}: {ins}. Returning raw content or default.")
            if file_not_found:
                last_read_status = "FILE_NOT_FOUND"
                return inval, False
            last_read_status = "SUCCESS"
            return inval, True
    except Exception as e:
        logger.error(f"Error parsing content from {file_path} ('{ins}'): {e}. Returning default.")
        if file_not_found:
            last_read_status = "FILE_NOT_FOUND"
        else:
            last_read_status = "PARSE_ERROR"
        return default_return_val, False


def write(mod, port_identifier, name, val, delta=0):
    """
    Write data either to ZMQ port or file.
    `val` is the data payload (list or string); write() prepends [simtime + delta] internally.
    """
    # Case 1: ZMQ port
    if isinstance(port_identifier, str) and port_identifier in mod.zmq_ports:
        zmq_p = mod.zmq_ports[port_identifier]
        try:
            # Keep ZMQ payloads JSON-serializable by normalizing numpy types.
            zmq_val = convert_numpy_to_python(val)
            if isinstance(zmq_val, list):
                # Prepend simtime to match file-based write behavior
                payload = [mod.simtime + delta] + zmq_val
                zmq_p.send_json_with_retry(payload)
                # simtime must not be mutated here.
                # Mutation breaks cross-language determinism (see issue #385).
            else:
                zmq_p.send_json_with_retry(zmq_val)
        except zmq.error.ZMQError as e:
            logger.error(f"ZMQ write error on port {port_identifier} (name: {name}): {e}")
        except Exception as e:
            logger.error(f"Unexpected error during ZMQ write on port {port_identifier} (name: {name}): {e}")
        return
    
    # Case 2: File-based port
    try:
        file_port_num = int(port_identifier)
        port_dir = mod._port_path(mod.outpath, file_port_num)
        file_path = os.path.join(port_dir, name) 
    except ValueError:
        logger.error(f"Error: Invalid port identifier '{port_identifier}' for file operation. Must be integer or ZMQ name.")
        return

    # File writing rules
    if isinstance(val, str):
        time.sleep(2 * mod.delay) # string writes wait longer
    elif not isinstance(val, list):
        logger.error(f"File write to {file_path} must have list or str value, got {type(val)}")
        return

    try:
        with open(file_path, "w") as outfile:
            if isinstance(val, list):
                # Convert numpy types to native Python types
                val_converted = convert_numpy_to_python(val)
                data_to_write = [mod.simtime + delta] + val_converted
                outfile.write(str(data_to_write))
                # simtime must not be mutated here.
                # Mutation breaks cross-language determinism (see issue #385).
            else: 
                outfile.write(val)
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")

def initval(mod, simtime_val_str): 
    """
    Initialize simtime from string containing a list.
    Example: "[10, 'foo', 'bar']" -> simtime=10, returns ['foo','bar']
    """
    try:
        val = literal_eval(simtime_val_str)
        if isinstance(val, list) and len(val) > 0:
            first_element = val[0]
            if isinstance(first_element, (int, float)):
                mod.simtime = first_element
                return val[1:] 
            else:
                logger.error(f"Error: First element in initval string '{simtime_val_str}' is not a number. Using data part as is or empty.")
                return val[1:] if len(val) > 1 else [] 
        else: 
            logger.error(f"Error: initval string '{simtime_val_str}' is not a list or is empty. Returning empty list.")
            return []

    except Exception as e:
        logger.error(f"Error parsing simtime_val_str '{simtime_val_str}': {e}. Returning empty list.")
        return []
