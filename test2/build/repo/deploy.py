import os
import pynja
from .root_paths import *

class DeployVariant(pynja.Variant):
    def __init__(self, string):
        super().__init__(string, self.get_field_defs())

    def get_field_defs(self):
        fieldDefs = [
            "product",      [ "app32", "app64", "sdk" ],
            "config",       [ "dbg", "rel" ],
        ]
        return fieldDefs

class DeployProject(pynja.DeployProject):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        if not isinstance(variant, DeployVariant):
            raise Exception("variant must be instanceof(DeployVariant)")

    def get_project_dir(self):
        return getattr(rootPaths, type(self).__name__)

    def get_project_rel_dir(self):
        return getattr(rootPathsRel, type(self).__name__)

    def get_built_dir(self):
        return os.path.join(rootPaths.built, self.get_project_rel_dir(), str(self.variant))
