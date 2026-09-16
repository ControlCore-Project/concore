import os


def has_concore_markers(cwd):
    """True only if `cwd` looks like an actual concore-generated node
    working directory, i.e. it contains the runtime files mkconcore.py
    copies into every generated study (concore.iport/oport plus the
    runtime module itself)."""
    if not cwd:
        return False
    try:
        if not os.path.isfile(os.path.join(cwd, "concore.iport")):
            return False
        return os.path.isfile(os.path.join(cwd, "concore.py")) or os.path.isfile(
            os.path.join(cwd, "concoredocker.py")
        )
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
    if any(os.path.basename(str(item)).lower() == "concorekill.bat" for item in cmdline):
        return True
    return has_concore_markers(cwd)
