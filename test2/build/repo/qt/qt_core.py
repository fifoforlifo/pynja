import os
import pynja
import repo

# This is a pseudo-projects that makes linking against Qt easier.
# There is no output here, just linkLibraries and runtimeDeps variables being set.

@pynja.project
class qt_core(repo.CppProject):
    def emit(self):
        if self.variant.linkage == "sta":
            raise Exception("Qt static libs not supported.")
        self.qt_add_lib_dependency("Qt5Core")
        self.qt_add_lib_dependency("icuin49", staticLink=False, forceRelease=True)
        self.qt_add_lib_dependency("icuuc49", staticLink=False, forceRelease=True)
        self.qt_add_lib_dependency("icudt49", staticLink=False, forceRelease=True)

        self.propagate_lib_dependencies()
