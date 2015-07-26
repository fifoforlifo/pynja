import os
from .tc import *
from . import build


class CppToolChain(build.ToolChain):
    def __init__(self, name, isTargetWindows):
        super().__init__(name)
        self.isTargetWindows = isTargetWindows
        self.defaultCppOptions = []     # applies to every compile
        self.defaultLinkOptions = []    # applies to every link
