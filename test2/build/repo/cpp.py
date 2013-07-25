import os
import pynja
from .root_paths import *


# just hack a global instance here -- it assumes protoc is in the PATH
protocToolChain = pynja.ProtocToolChain("protoc")


class CppVariant(pynja.Variant):
    def __init__(self, string):
        super().__init__(string, self.get_field_defs())

    def get_field_defs(self):
        if os.name == 'nt':
            fieldDefs = [
                "os",           [ "windows" ],
                "toolchain",    [ "msvc8", "msvc9", "msvc10", "msvc11", "mingw", "mingw64", "nvcc_msvc10", "nvcc_msvc11"  ],
                "arch",         [ "x86", "amd64" ],
                "config",       [ "dbg", "rel" ],
                "crt",          [ "scrt", "dcrt" ],
            ]
            return fieldDefs
        elif os.name == 'posix':
            fieldDefs = [
                "os",           [ "linux" ],
                "toolchain",    [ "gcc", "clang" ],
                "arch",         [ "x86", "amd64" ],
                "config",       [ "dbg", "rel" ],
                "crt",          [ "scrt", "dcrt" ],
            ]
            return fieldDefs
        else:
            raise Exception("Not implemented")


class CppProject(pynja.CppProject):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        if not isinstance(variant, CppVariant):
            raise Exception("variant must be instanceof(CppVariant)")
        if self.variant.os == "windows":
            self.winsdkVer = 80

        if self.variant.toolchain == 'msvc11' and self.variant.arch == 'amd64':
            self.qtBinDir = rootPaths.qt5vc11BinDir
            self.qtBuiltDir = os.path.join(self.builtDir, "qt")
            self.qtIncludePaths = [
                os.path.normpath(os.path.join(self.qtBinDir, "..", "include")),
                self.qtBuiltDir,
            ]
            self.qtLibDir = os.path.normpath(os.path.join(self.qtBinDir, "..", "lib"))
            self.qtToolChain = self.projectMan.get_toolchain('qt5vc11')

    def get_toolchain(self):
        toolchainName = "%s-%s" % (self.variant.toolchain, self.variant.arch)
        toolchain = self.projectMan.get_toolchain(toolchainName)
        if not toolchain:
            raise Exception("Could not find toolchain " + toolchainName)
        return toolchain

    def get_project_dir(self):
        return getattr(rootPaths, type(self).__name__)

    def get_project_rel_dir(self):
        return getattr(rootPaths, type(self).__name__ + "_rel")

    def get_built_dir(self):
        return os.path.join(rootPaths.built, self.get_project_rel_dir(), str(self.variant))

    def set_gcc_machine_arch(self, task):
        if ("gcc" in self.variant.toolchain) or ("mingw" in self.variant.toolchain):
            if self.variant.arch == "x86":
                task.addressModel = "-m32"
            elif self.variant.arch == "amd64":
                task.addressModel = "-m64"

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.extraDeps.extend(self._forcedDeps)
        task.phonyTarget = os.path.basename(task.sourcePath)
        if self.variant.os == "windows":
            if "msvc" in self.variant.toolchain:
                task.dynamicCRT = (self.variant.crt == 'dcrt')
                winsdkDir = self.calc_winsdk_dir()
                if self.winsdkVer < 80:
                    task.includePaths.append(os.path.join(winsdkDir, "Include"))
                else:
                    task.includePaths.append(os.path.join(winsdkDir, "Include", "shared"))
                    task.includePaths.append(os.path.join(winsdkDir, "Include", "um"))

        self.set_gcc_machine_arch(task)

        task.debugLevel = 2;
        if self.variant.config == "dbg":
            task.optLevel = 0
        elif self.variant.config == "rel":
            task.optLevel = 3
            if not task.createPCH:
                task.lto = self.toolchain.ltoSupport

        if isinstance(self.toolchain, pynja.ClangToolChain):
            task.extraOptions.append("-fcolor-diagnostics")

    def make_static_lib(self, name):
        name = os.path.normpath(name)
        if "msvc" in self.variant.toolchain:
            outputPath = os.path.join(self.builtDir, name + ".lib")
        else:
            outputPath = os.path.join(self.builtDir, "lib" + name + ".a")
        task = super().make_static_lib(outputPath)
        task.phonyTarget = name
        return task

    def make_shared_lib(self, name):
        name = os.path.normpath(name)
        if self.variant.os == "windows":
            outputPath = os.path.join(self.builtDir, name + ".dll")
            if "msvc" in self.variant.toolchain:
                libraryPath = os.path.join(self.builtDir, name + ".lib")
            elif "mingw" in self.variant.toolchain:
                libraryPath = outputPath # mingw can link directly against DLLs -- no implib needed
        else:
            outputPath = os.path.join(self.builtDir, "lib" + name + ".so")
            libraryPath = outputPath
        task = super().make_shared_lib(outputPath, libraryPath)
        task.phonyTarget = name

        if self.variant.config == 'rel':
            task.lto = self.toolchain.ltoSupport

        return task

    def make_executable(self, name):
        name = os.path.normpath(name)
        if self.variant.os == "windows":
            outputPath = os.path.join(self.builtDir, name + ".exe")
        else:
            outputPath = os.path.join(self.builtDir, name)
        task = super().make_executable(outputPath)
        task.phonyTarget = name

        if self.variant.config == 'rel':
            task.lto = self.toolchain.ltoSupport

        return task

    def calc_winsdk_dir(self):
        name = 'winsdk' + str(self.winsdkVer)
        return getattr(rootPaths, name)

    def calc_winsdk_lib_dir(self):
        winsdkDir = self.calc_winsdk_dir()
        if self.winsdkVer < 80:
            if self.variant.arch == "x86":
                return os.path.join(winsdkDir, "Lib")
            elif self.variant.arch == "amd64":
                return os.path.join(winsdkDir, "Lib", "x64")
            else:
                raise Exception("unsupported arch: " + self.variant.arch)
        else:
            if self.variant.arch == "x86":
                return os.path.join(winsdkDir, "Lib", "win8", "um", "x86")
            elif self.variant.arch == "amd64":
                return os.path.join(winsdkDir, "Lib", "win8", "um", "x64")
            else:
                raise Exception("unsupported arch: " + self.variant.arch)

    def add_platform_libs(self, task):
        if self.variant.os == "windows":
            if "msvc" in self.variant.toolchain:
                winsdkLibDir = self.calc_winsdk_lib_dir()
                self.add_input_lib(os.path.join(winsdkLibDir, "kernel32.lib"))
                self.add_input_lib(os.path.join(winsdkLibDir, "user32.lib"))
                self.add_input_lib(os.path.join(winsdkLibDir, "gdi32.lib"))
                self.add_input_lib(os.path.join(winsdkLibDir, "uuid.lib"))

    def set_shared_lib_options(self, task):
        super().set_shared_lib_options(task)
        self.set_gcc_machine_arch(task)
        task.keepDebugInfo = True
        self.add_platform_libs(task)

    def set_executable_options(self, task):
        super().set_executable_options(task)
        self.set_gcc_machine_arch(task)
        task.keepDebugInfo = True
        self.add_platform_libs(task)


    # protoc

    def _protoc_one(self, sourcePath, language):
        task = pynja.ProtocTask(self, sourcePath, self.builtDir, self.projectDir, language, protocToolChain)
        self.set_protoc_options(task)
        self._forcedDeps.add(task.outputHeader)
        return task

    def protoc(self, filePaths, language):
        if isinstance(filePaths, str):
            return self._protoc_one(filePaths, language)
        else:
            taskList = []
            for filePath in filePaths:
                task = self._protoc_one(filePath, language)
                taskList.append(task)
            tasks = pynja.BuildTasks(taskList)
            return tasks

    def protoc_cpp_compile(self, filePaths):
        proto_sources = []
        with self.protoc(filePaths, 'cpp') as tasks:
            for task in tasks:
                proto_sources.append(task.outputPath)
            self.cpp_compile(proto_sources)
        return proto_sources

    def set_protoc_options(self, task):
        pass


    # qt

    def _qt_uic_one(self, sourcePath):
        (barename, ext) = os.path.splitext(os.path.basename(sourcePath))
        outputPath = os.path.join(self.qtBuiltDir, "ui_" + barename + ".h")
        if not os.path.isabs(sourcePath):
            sourcePath = os.path.join(self.projectDir, sourcePath)
        task = pynja.qt.QtUiTask(self, sourcePath, outputPath, self.projectDir, self.qtToolChain)
        self._forcedDeps.add(outputPath)
        return task

    def qt_uic(self, filePaths):
        with self.qt_uic_ex(filePaths) as tasks:
            pass
        return tasks

    def qt_uic_ex(self, filePaths):
        if isinstance(filePaths, str):
            return self._qt_uic_one(filePaths)
        else:
            taskList = []
            for filePath in filePaths:
                task = self._qt_uic_one(filePath)
                taskList.append(task)
            tasks = pynja.BuildTasks(taskList)
            return tasks

    def _qt_moc_one(self, sourcePath):
        (barename, ext) = os.path.splitext(os.path.basename(sourcePath))
        ext = ext.lower()
        isHeader = (ext == '.h' or ext == '.hpp' or ext == '.hxx')
        if isHeader:
            outputPath = os.path.join(self.qtBuiltDir, "moc_" + barename + ".cpp")
        else:
            outputPath = os.path.join(self.qtBuiltDir, barename + ".moc")
        if not os.path.isabs(sourcePath):
            sourcePath = os.path.join(self.projectDir, sourcePath)
        task = pynja.qt.QtMocTask(self, sourcePath, outputPath, self.projectDir, self.qtToolChain)
        if not isHeader:
            task.emitInclude = False
        self.set_qt_moc_options(task)
        return task

    def qt_moc(self, filePaths):
        with self.qt_moc_ex(filePaths) as tasks:
            pass
        return tasks

    def qt_moc_ex(self, filePaths):
        if isinstance(filePaths, str):
            return self._qt_moc_one(filePaths)
        else:
            taskList = []
            for filePath in filePaths:
                task = self._qt_moc_one(filePath)
                taskList.append(task)
            tasks = pynja.BuildTasks(taskList)
            return tasks

    def qt_moc_cpp_compile(self, filePaths):
        tasks = self.qt_moc(filePaths)
        moc_includables = [] # *.moc, which are 'includable' in a cpp but not quite headers :)
        for task in tasks:
            basename = os.path.basename(task.outputPath)
            if basename.startswith("moc_"):
                self.cpp_compile(task.outputPath)
            else:
                moc_includables.append(task.outputPath)
        self._forcedDeps.update(moc_includables)

    def set_qt_moc_options(self, task):
        pass

    def qt_add_lib_dependency(self, libName, staticLink=True, forceRelease=False):
        # qt only enabled on this variant because the test machine only has this version of Qt available
        if self.variant.toolchain == 'msvc11' and self.variant.arch == 'amd64':
            if not forceRelease and self.variant.config == 'dbg':
                libName = libName + 'd'
            if staticLink:
                libFilePath = os.path.join(self.qtLibDir, libName + '.lib')
                self.add_input_lib(libFilePath)
            self.add_runtime_dependency(os.path.join(self.qtBinDir, libName + '.dll'))
