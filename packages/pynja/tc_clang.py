from .tc_gcc import *

class ClangToolChain(GccToolChain):
    def __init__(self, name, installDir, targetWindows, prefix = None, suffix = None):
        super().__init__(name, installDir, targetWindows, prefix, suffix)
        self.ccName = "clang"
        self.pchFileExt = ".pch"
