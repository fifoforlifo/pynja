import os
import re
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
            fieldDefs = [
                "os",           [ "linux" ],
                "toolchain",    [ "gcc" ],
                "arch",         [ "x86", "amd64" ],
                "config",       [ "dbg", "rel" ],
                "crt",          [ "scrt", "dcrt" ],
            ]
            return fieldDefs
        else:
            raise Exception("Not implemented")


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

    def set_gcc_machine_arch(self, task):
        if re.match("(mingw)|(gcc)", self.variant.toolchain):
            if self.variant.arch == "x86":
                task.addressModel = "-m32"
            elif self.variant.arch == "amd64":
                task.addressModel = "-m64"

    def set_cpp_compile_options(self, task):
        task.phonyTarget = os.path.basename(task.sourcePath)
        if self.variant.os == "windows":
            if self.variant.toolchain.startswith("msvc"):
                task.includePaths.append(upynja.rootPaths.winsdk + "/Include")
                task.dynamicCRT = (self.variant.crt == 'dcrt')

        self.set_gcc_machine_arch(task)

        task.debugLevel = 2;
        if self.variant.config == "dbg":
            task.optLevel = 0
            task.minimalRebuild = True
        elif self.variant.config == "rel":
            task.optLevel = 3

    def make_static_lib(self, name):
        if self.variant.toolchain.startswith("msvc"):
            outputPath = os.path.join(self.builtDir, name + ".lib")
        else:
            outputPath = os.path.join(self.builtDir, "lib" + name + ".a")
        task = super().make_static_lib(outputPath)
        task.phonyTarget = name
        return task

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
        task = super().make_shared_lib(outputPath, libraryPath)
        task.phonyTarget = name
        return task

    def make_executable(self, name):
        if self.variant.os == "windows":
            outputPath = os.path.join(self.builtDir, name + ".exe")
        else:
            outputPath = os.path.join(self.builtDir, name)
        task = super().make_executable(outputPath)
        task.phonyTarget = name
        return task

    def calc_winsdk_dir(self):
        if self.variant.arch == "x86":
            return upynja.rootPaths.winsdk + "/Lib"
        elif self.variant.arch == "amd64":
            return upynja.rootPaths.winsdk + "/Lib/x64"
        else:
            raise Exception("unsupported arch: " + self.variant.arch)

    def add_platform_libs(self, task):
        if self.variant.os == "windows":
            if self.variant.toolchain.startswith("msvc"):
                winsdkLibDir = self.calc_winsdk_dir()
                task.inputs.append(os.path.join(winsdkLibDir, "kernel32.lib"))
                task.inputs.append(os.path.join(winsdkLibDir, "user32.lib"))
                task.inputs.append(os.path.join(winsdkLibDir, "gdi32.lib"))

    def set_shared_lib_options(self, task):
        self.set_gcc_machine_arch(task)
        task.keepDebugInfo = True
        self.add_platform_libs(task)

    def set_executable_options(self, task):
        self.set_gcc_machine_arch(task)
        task.keepDebugInfo = True
        self.add_platform_libs(task)
