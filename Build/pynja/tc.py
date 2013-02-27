import os
import pynja.build

class GccToolChain(pynja.build.ToolChain):
    """A toolchain object capable of driving gcc and mingw"""

    def __init__(self, name, installDir, prefix = None, suffix = None):
        super().__init__(name)
        self.installDir = installDir
        self.prefix = prefix
        self.suffix = suffix
        self._scriptDir = os.path.join(os.path.dirname(__file__), "gcc")
        self._cxx_script = os.path.join(self._scriptDir, "gcc-cxx-invoke.py")
        self._lib_script = os.path.join(self._scriptDir, "gcc-lib-invoke.py")
        self._lnk_script = os.path.join(self._scriptDir, "gcc-lnk-invoke.py")
        pass

    pass


if os.name == "nt":
    # define MSVC toolchain

    class MsvcToolChain(pynja.build.ToolChain):
        """A toolchain object capable of driving msvc 8.0 and greater."""

        def __init__(self, name, installDir, arch):
            super().__init__(name)
            self.installDir = installDir
            self.arch = arch
            self._scriptDir = os.path.join(os.path.dirname(__file__), "msvc")
            self._cxx_script = os.path.join(self._scriptDir, "msvc-cxx-invoke.py")
            self._lib_script = os.path.join(self._scriptDir, "msvc-lib-invoke.py")
            self._lnk_script = os.path.join(self._scriptDir, "msvc-lnk-invoke.py")
            pass

        def emit_rules(self, file):
            pass
