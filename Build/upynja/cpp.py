import os
import pynja
import upynja

class CppProject(pynja.cpp.CppProject):
    def get_project_dir(self):
        return upynja.rootPaths[self.__name__]

    def get_built_dir(self):
        os.path.join(upynja.rootPaths["Built"], upynja.rootPaths[self.__name__ + "_rel"], self.variant.str)
