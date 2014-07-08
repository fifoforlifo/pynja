import os
from .tc import *
from . import build


class CppToolChain(build.ToolChain):
    def __init__(self, name, targetWindows):
        super().__init__(name)
        self.targetWindows = targetWindows
