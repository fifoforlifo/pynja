from .tc_gcc import *

class ClangToolChain(GccToolChain):
    def __init__(self, name, installDir, isTargetWindows, prefix = None, suffix = None):
        super().__init__(name, installDir, isTargetWindows, prefix, suffix)
        self.ccName = "clang"
        self.pchFileExt = ".pch"
