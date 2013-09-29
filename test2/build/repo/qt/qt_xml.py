import os
import pynja
import repo

# This is a pseudo-projects that makes linking against Qt easier.
# There is no output here, just linkLibraries and runtimeDeps variables being set.

@pynja.project
class qt_xml(repo.CppProject):
    def emit(self):
        if self.variant.linkage == "sta":
            raise Exception("Qt static libs not supported.")
        self.qt_add_lib_dependency("Qt5Xml")
        self.add_cpplib_dependency("qt_core")
        self.propagate_lib_dependencies()
