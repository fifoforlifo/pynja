import os
import pynja
import upynja


class CppVariant(pynja.build.Variant):
    def __init__(self, string):
        super().__init__(string, self.get_field_defs())

    def get_field_defs(self):
        if os.name == 'nt':
            fieldDefs = [
                "os",           [ "windows" ],
                "toolchain",    [ "msvc8", "msvc9", "msvc10", "msvc11", "mingw", "mingw64" ],
                "arch",         [ "x86", "amd64" ],
                "config",       [ "dbg", "rel" ],
                "crt",          [ "scrt", "dcrt" ],
            ]
            return fieldDefs
        elif os.name == 'posix':
            raise NotImplemented()
        else:
            raise NotImplemented()


class CppProject(pynja.cpp.CppProject):
    def get_toolchain(self):
        toolchainName = "%s-%s" % (self.variant.toolchain, self.variant.arch)
        toolchain = self.projectMan.get_toolchain(toolchainName)
        if not toolchain:
            raise Exception("Could not find toolchain " + toolchainName)
        return toolchain

    def get_project_dir(self):
        return getattr(upynja.rootPaths, self.__class__.__name__)

    def get_built_dir(self):
        return os.path.join(upynja.rootPaths.built, getattr(upynja.rootPaths, self.__class__.__name__ + "_rel"), self.variant.str)

    def make_static_lib(self, name):
        if self.variant.toolchain.startswith("msvc"):
            outputPath = os.path.join(self.builtDir, name + ".lib")
        else:
            outputPath = os.path.join(self.builtDir, "lib" + name + ".a")
        return super().make_static_lib(outputPath)

    def make_shared_lib(self, name):
        if self.variant.os == "windows":
            outputPath = os.path.join(self.builtDir, name + ".dll")
            if self.variant.toolchain.startswith("msvc"):
                libraryPath = os.path.join(self.builtDir, name + ".lib")
            elif self.variant.toolchain.startswith("mingw"):
                libraryPath = outputPath # mingw can link directly against DLLs -- no implib needed
        else:
            outputPath = os.path.join(self.builtDir, "lib" + name + ".so")
            libraryPath = outputPath
        return super().make_shared_lib(outputPath, libraryPath)

    def make_executable(self, name):
        if self.variant.os == "windows":
            outputPath = os.path.join(self.builtDir, name + ".exe")
        else:
            outputPath = os.path.join(self.builtDir, name)
        return super().make_executable(outputPath)
