"""
Backward-compatibility wrapper for pidmayuresh.py.

This file previously contained a duplicate PID controller implementation
that used print() instead of logging.  The canonical implementation now
lives in pidmayuresh.py (which uses the logging module).

This wrapper re-exports everything so that any existing import of
pidmayuresh3 continues to work without modification.

See:  https://github.com/ControlCore-Project/concore/issues/378
"""

import warnings
warnings.warn(
    "pidmayuresh3 is deprecated — use pidmayuresh instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-execute the canonical module so run-time behaviour is identical
# when this file is invoked directly (e.g., via a study graph).
try:
    # Prefer relative import when part of the tools package
    from .pidmayuresh import *  # type: ignore[attr-defined]  # noqa: F401,F403
except ImportError:
    # Fallback for script-style execution (e.g., `python tools/pidmayuresh3.py`)
    from pidmayuresh import *  # noqa: F401,F403



