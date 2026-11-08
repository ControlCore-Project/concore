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

_LOCK_LEN = 0x7FFFFFFF  # lock range large enough to cover entire file
_BASE_DIR = os.path.abspath(".")  # capture CWD before atexit can shift it
_PID_REGISTRY_FILE = os.path.join(_BASE_DIR, "concorekill_pids.txt")
_KILL_SCRIPT_FILE = os.path.join(_BASE_DIR, "concorekill.bat")

def _current_pid_record():
    """Return current PID and process creation time in Unix milliseconds."""
    import psutil
    process = psutil.Process(os.getpid())
    start_time_ms = int(process.create_time() * 1000)
    return f"{process.pid}|{start_time_ms}"
def _register_pid():
    """Append current process identity to the shared registry."""
    import psutil
    try:
        record = _current_pid_record()
        with open(_PID_REGISTRY_FILE, "a") as f:
            if hasattr(sys, 'getwindowsversion'):
                import msvcrt
                try:
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, _LOCK_LEN)
                    f.write(record + "\n")
                    f.flush()
                finally:
                    try:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, _LOCK_LEN)
                    except (OSError, ValueError):
                        pass
            else:
                f.write(record + "\n")
    except (OSError, psutil.Error):
        pass
def _cleanup_pid():
    """Remove current process entries while preserving the shared files."""
    pid = str(os.getpid())
    try:
        if not os.path.exists(_PID_REGISTRY_FILE):
            return
        with open(_PID_REGISTRY_FILE, "r+") as f:
            is_windows = hasattr(sys, "getwindowsversion")
            if is_windows:
                import msvcrt
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, _LOCK_LEN)
            try:
                f.seek(0)
                entries = [line.strip() for line in f if line.strip()]
                remaining = [
                    entry for entry in entries
                    if entry.split("|", 1)[0].strip() != pid
                ]
                f.seek(0)
                f.truncate()
                for entry in remaining:
                    f.write(entry + "\n")
                f.flush()
            finally:
                if is_windows:
                    try:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, _LOCK_LEN)
                    except (OSError, ValueError):
                        pass
    except OSError:
        pass

def _write_kill_script():
    """Generate a batch launcher for the shared PowerShell cleanup helper."""
    try:
        helper_name = "concorekill.ps1"
        script = (
            "@echo off\r\n"
            "setlocal\r\n"
            'if not exist "%~dp0' + helper_name + '" (\r\n'
            '    echo Missing process cleanup helper: "%~dp0' + helper_name + '"\r\n'
            "    exit /b 1\r\n"
            ")\r\n"
            'powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0' + helper_name + '"\r\n'
            "exit /b %ERRORLEVEL%\r\n"
        )
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

    Returns only the data payload for backward compatibility.
    Use ``read_with_status()`` for explicit ``(data, success_flag)``.
    """
    global last_read_status
    result, _ok = concore_base.read(_mod, port_identifier, name, initstr_val)
    last_read_status = concore_base.last_read_status
    return result


def read_with_status(port_identifier, name, initstr_val):
    """Read data and return ``(data, success_flag)``.

    Also updates ``concore.last_read_status``.
    """
    global last_read_status
    result = concore_base.read(_mod, port_identifier, name, initstr_val)
    last_read_status = concore_base.last_read_status
    return result


def write(port_identifier, name, val, delta=0):
    concore_base.write(_mod, port_identifier, name, val, delta)

def initval(simtime_val_str): 
    return concore_base.initval(_mod, simtime_val_str)
