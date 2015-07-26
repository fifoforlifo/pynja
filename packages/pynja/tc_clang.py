from .tc_gcc import *
from .tc_msvc import *

class ClangToolChain(GccToolChain):
    def __init__(self, name, installDir, isTargetWindows, prefix = None, suffix = None):
        super().__init__(name, installDir, isTargetWindows, prefix, suffix)
        self.ccName = "clang"
        self.pchFileExt = ".pch"

if os.name == "nt":
    class ClangMsvcToolChain(MsvcToolChain):
        def __init__(self, name, msvcInstallDir, arch, msvcVer, llvmDir):
            super().__init__(name, msvcInstallDir, arch, msvcVer)
            self._cxx_script  = os.path.join(self._scriptDir, "clang_msvc-cxx-invoke.py")
            self._cxx_script_extra_args = '"%s"' % llvmDir
