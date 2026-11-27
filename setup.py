import glob
import os

from setuptools import setup
from setuptools.command.build_py import build_py

# Files mkconcore.py reads from next to itself (CONCOREPATH) and copies into
# every generated study. They are not Python modules, so setuptools would
# otherwise leave them out of the wheel and `concore build` could not work
# from a regular (non-editable) install. Keep MANIFEST.in in sync.
RUNTIME_FILE_PATTERNS = [
    "concore*.hpp",
    "concore*.v",
    "concore*.java",
    "ConcoreJavaRuntimeCore.java",
    "concore*.jl",
    "concore_default_maxtime.m",
    "concore_initval.m",
    "concore_iport.m",
    "concore_literal_eval.m",
    "concore_literal_serialize.m",
    "concore_oport.m",
    "concore_read.m",
    "concore_unchanged.m",
    "concore_write.m",
    "import_concore.m",
    "import_concoredocker.m",
    "Dockerfile.*",
    "mkcompile",
    "concore.octave",
    "concore.mcr",
    "concore.sudo",
    "concore.repo",
    "concore.tools",
    "tools/extract_graphml.py",
]


class build_py_with_runtime_files(build_py):
    """Install the runtime files next to mkconcore.py in the built package."""

    def run(self):
        super().run()
        if self.dry_run:
            return
        for pattern in RUNTIME_FILE_PATTERNS:
            for src in sorted(glob.glob(pattern)):
                dest = os.path.join(self.build_lib, src)
                self.mkpath(os.path.dirname(dest))
                self.copy_file(src, dest)


# All other metadata and configuration is in pyproject.toml.
setup(cmdclass={"build_py": build_py_with_runtime_files})
