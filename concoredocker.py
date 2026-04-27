import time
from ast import literal_eval
import re
import os
import logging
import atexit
import sys
import zmq
import numpy as np
import signal

import concore_base

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

ZeroMQPort = concore_base.ZeroMQPort
convert_numpy_to_python = concore_base.convert_numpy_to_python
safe_literal_eval = concore_base.safe_literal_eval
parse_params = concore_base.parse_params

# Global variables
zmq_ports = {}
_cleanup_in_progress = False

last_read_status = "SUCCESS"

s = ''
olds = ''
delay = 1
retrycount = 0
inpath = os.path.abspath("/in")
outpath = os.path.abspath("/out")
simtime = 0

def _port_path(base, port_num):
    return os.path.join(base, str(port_num))

concore_params_file = os.path.join(_port_path(inpath, 1), "concore.params")
concore_maxtime_file = os.path.join(_port_path(inpath, 1), "concore.maxtime")

# Load input/output ports if present
iport = safe_literal_eval("concore.iport", {})
oport = safe_literal_eval("concore.oport", {})

_mod = sys.modules[__name__]

# ===================================================================
# ZeroMQ Communication Wrapper
# ===================================================================
def init_zmq_port(port_name, port_type, address, socket_type_str):
    concore_base.init_zmq_port(_mod, port_name, port_type, address, socket_type_str)

def terminate_zmq():
    """Clean up all ZMQ sockets and contexts before exit."""
    concore_base.terminate_zmq(_mod)

def signal_handler(sig, frame):
    """Handle interrupt signals gracefully."""
    print(f"\nReceived signal {sig}, shutting down gracefully...")
    try:
        atexit.unregister(terminate_zmq)
    except Exception:
        pass
    concore_base.terminate_zmq(_mod)
    sys.exit(0)

# Register cleanup handlers (docker containers receive SIGTERM from docker stop)
atexit.register(terminate_zmq)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

params = concore_base.load_params(concore_params_file)

#9/30/22
def tryparam(n, i):
    return params.get(n, i)

#9/12/21
def default_maxtime(default):
    global maxtime
    maxtime = safe_literal_eval(concore_maxtime_file, default)

default_maxtime(100)

def unchanged():
    return concore_base.unchanged(_mod)

# ===================================================================
# I/O Handling (File + ZMQ)
# ===================================================================
def read(port_identifier, name, initstr_val):
    global last_read_status
    result, _ok = concore_base.read(_mod, port_identifier, name, initstr_val)
    last_read_status = concore_base.last_read_status
    return result

def read_with_status(port_identifier, name, initstr_val):
    global last_read_status
    result = concore_base.read(_mod, port_identifier, name, initstr_val)
    last_read_status = concore_base.last_read_status
    return result

def write(port_identifier, name, val, delta=0):
    concore_base.write(_mod, port_identifier, name, val, delta)

def initval(simtime_val):
    return concore_base.initval(_mod, simtime_val)
