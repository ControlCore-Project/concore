import time
import logging
import os
import atexit
from ast import literal_eval
import sys
import re
import zmq
import numpy as np
import signal

import concore_base

logger = logging.getLogger('concore')
logger.addHandler(logging.NullHandler())

#these lines mute the noisy library
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING) 
logging.getLogger('requests').setLevel(logging.WARNING) 


# if windows, register this process PID for safe termination
# Previous approach: single "concorekill.bat" overwritten by each node (race condition).
# New approach: append PID to shared registry; generate validated kill script.
# See: https://github.com/ControlCore-Project/concore/issues/391

_PID_REGISTRY_FILE = "concorekill_pids.txt"
_KILL_SCRIPT_FILE = "concorekill.bat"

def _register_pid():
    """Append current PID to the shared registry file."""
    try:
        with open(_PID_REGISTRY_FILE, "a") as f:
            f.write(str(os.getpid()) + "\n")
    except OSError:
        pass

def _cleanup_pid():
    """Remove current PID from registry on exit. Uses file locking on Windows."""
    pid = str(os.getpid())
    try:
        if not os.path.exists(_PID_REGISTRY_FILE):
            return
        with open(_PID_REGISTRY_FILE, "r+") as f:
            if hasattr(sys, 'getwindowsversion'):
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            pids = [line.strip() for line in f if line.strip()]
            remaining = [p for p in pids if p != pid]
            if remaining:
                f.seek(0)
                f.truncate()
                for p in remaining:
                    f.write(p + "\n")
            else:
                f.close()
                try:
                    os.remove(_PID_REGISTRY_FILE)
                except OSError:
                    pass
                try:
                    os.remove(_KILL_SCRIPT_FILE)
                except OSError:
                    pass
    except OSError:
        pass

def _write_kill_script():
    """Generate concorekill.bat that validates each PID before killing."""
    try:
        script = "@echo off\r\n"
        script += 'if not exist "%~dp0' + _PID_REGISTRY_FILE + '" (\r\n'
        script += "    echo No PID registry found. Nothing to kill.\r\n"
        script += "    exit /b 0\r\n"
        script += ")\r\n"
        script += 'for /f "usebackq tokens=*" %%p in ("%~dp0' + _PID_REGISTRY_FILE + '") do (\r\n'
        script += '    tasklist /FI "PID eq %%p" 2>nul | find /i "python" >nul\r\n'
        script += "    if not errorlevel 1 (\r\n"
        script += "        echo Killing Python process %%p\r\n"
        script += "        taskkill /F /PID %%p >nul 2>&1\r\n"
        script += "    ) else (\r\n"
        script += "        echo Skipping PID %%p - not a Python process or not running\r\n"
        script += "    )\r\n"
        script += ")\r\n"
        script += 'del /q "%~dp0' + _PID_REGISTRY_FILE + '" 2>nul\r\n'
        script += 'del /q "%~dp0' + _KILL_SCRIPT_FILE + '" 2>nul\r\n'
        with open(_KILL_SCRIPT_FILE, "w", newline="") as f:
            f.write(script)
    except OSError:
        pass

if hasattr(sys, 'getwindowsversion'):
    _register_pid()
    _write_kill_script()
    atexit.register(_cleanup_pid)

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
inpath = "./in" #must be rel path for local
outpath = "./out"
simtime = 0

def _port_path(base, port_num):
    return base + str(port_num)

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

# Register cleanup handlers
atexit.register(terminate_zmq)
signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
if not hasattr(sys, 'getwindowsversion'):
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination (Unix only)

params = concore_base.load_params(concore_params_file)

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
    return concore_base.unchanged(_mod)

# ===================================================================
# I/O Handling (File + ZMQ)
# ===================================================================
def read(port_identifier, name, initstr_val):
    """Read data from a ZMQ port or file-based port.

    Returns:
        tuple: (data, success_flag) where success_flag is True if real
            data was received, False if a fallback/default was used.
            Also sets ``concore.last_read_status`` to one of:
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
    result = concore_base.read(_mod, port_identifier, name, initstr_val)
    last_read_status = concore_base.last_read_status
    return result


def write(port_identifier, name, val, delta=0):
    concore_base.write(_mod, port_identifier, name, val, delta)

def initval(simtime_val_str): 
    return concore_base.initval(_mod, simtime_val_str)
