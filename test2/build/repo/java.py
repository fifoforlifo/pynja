import os
import re
import pynja
from .root_paths import *


class JavaVariant(pynja.Variant):
    def __init__(self, string):
        super().__init__(string, self.get_field_defs())

    def get_field_defs(self):
        fieldDefs = [
            "toolchain",    [ "javac"  ],
        ]
        return fieldDefs


class JavaProject(pynja.JavaProject):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)

    def get_toolchain(self):
        toolchainName = "%s" % (self.variant.toolchain)
        toolchain = self.projectMan.get_toolchain(toolchainName)
        if not toolchain:
            raise Exception("Could not find toolchain " + toolchainName)
        return toolchain

    def get_project_dir(self):
        return getattr(rootPaths, self.__class__.__name__)

    def get_built_dir(self):
        return os.path.join(rootPaths.built, getattr(rootPaths, self.__class__.__name__ + "_rel"), self.variant.str)
