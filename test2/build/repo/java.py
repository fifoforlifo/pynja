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
        if not isinstance(variant, JavaVariant):
            raise Exception("variant must be instanceof(JavaVariant)")

    def get_toolchain(self):
        toolchainName = "%s" % (self.variant.toolchain)
        toolchain = self.projectMan.get_toolchain(toolchainName)
        if not toolchain:
            raise Exception("Could not find toolchain " + toolchainName)
        return toolchain
