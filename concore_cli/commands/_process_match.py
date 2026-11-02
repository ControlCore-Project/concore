import ntpath
import os


# Runtime files mkconcore.py copies into a node folder, one set per language.
RUNTIME_FILES = (
    "concore.py",
    "concoredocker.py",
    "concore.hpp",
    "concoredocker.hpp",
    "concore.java",
    "concoredocker.java",
    "concore.v",
    "concoredocker.v",
    "concore_read.m",
)


def has_concore_markers(cwd):
    """True only if `cwd` looks like an actual concore-generated node
    working directory, i.e. it contains the runtime files mkconcore.py
    copies into every generated study (concore.iport/oport plus the
    runtime module for the node's language)."""
    if not cwd:
        return False
    try:
        if not os.path.isfile(os.path.join(cwd, "concore.iport")):
            return False
        return any(os.path.isfile(os.path.join(cwd, name)) for name in RUNTIME_FILES)
    except OSError:
        return False


def is_concore_process(cmdline, cwd):
    """Decide whether a process is an actual concore node process.

    A plain substring check like "concore" in the joined cmdline used to
    be used here, which matches anything launched from a directory that
    merely happens to have "concore" in its path (the default clone
    directory name for this repo among other things) and has nothing to
    do with concore at all. Instead, only match the generated kill
    script by exact filename, or a process whose working directory
    actually contains the concore runtime marker files.
    """
    # ntpath.basename splits on both "\\" and "/", so Windows paths are
    # handled the same regardless of the host OS.
    if any(ntpath.basename(str(item)).lower() == "concorekill.bat" for item in cmdline):
        return True
    return has_concore_markers(cwd)
