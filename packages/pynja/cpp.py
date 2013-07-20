import os
from abc import *
from . import build
import pynja.tc


class CppTask(build.BuildTask):
    def __init__(self, project, sourcePath, outputPath, workingDir):
        super().__init__(project)
        self.sourcePath = sourcePath
        self.outputPath = outputPath
        self.workingDir = workingDir
        # common compiler options
        self.extraOptions = []
        self.optLevel = 3
        self.debugLevel = 2
        self.warnLevel = 3
        self.warningsAsErrors = False
        self.includePaths = []
        self.defines = []
        self.createPCH = False
        self.usePCH = None # point this at a PCH file
        # gcc-specific
        self.addressModel = None # = {"-m32", "-m64"}
        self.std = None # see option -std within "C Dialect Options"
        self.lto = None
        # msvc-specific
        self.dynamicCRT = True
        self.asyncExceptionHandling = False
        self.externCNoThrow = True
        # nvcc-specific
        self.relocatableDeviceCode = True
        self.deviceDebugLevel = 1 # {0 = none, 1 = lineinfo, 2 = full [disables optimization]}
        # internal state tracking
        self._creatingPDB = False

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        toolchain.emit_cpp_compile(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


# Precompiled headers are always force-included via the commandline.
# If a toolchain does not support precompiled headers, then this
# dummy task is created, and the source header is force-included instead.
# Toolchains must also detect when the 'usePCH' attribute points at a header
# and handle it specially.
class DummyPchTask(CppTask):
    def __init__(self, project, sourcePath, workingDir):
        super().__init__(project, sourcePath, sourcePath, workingDir)

    # override emit() with a null implementation
    def emit(self):
        pass


class StaticLibTask(build.BuildTask):
    def __init__(self, project, outputPath, workingDir):
        super().__init__(project)
        self.outputPath = outputPath
        self.workingDir = workingDir
        self.inputs = []

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        self.inputs.extend(project._inputs)
        toolchain.emit_static_lib(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


class LinkTask(build.BuildTask):
    def __init__(self, project, outputPath, workingDir):
        super().__init__(project)
        self.extraOptions = []
        self.outputPath = outputPath
        self.outputLibraryPath = None
        self.workingDir = workingDir
        self.makeExecutable = True # if False, make shared library instead
        self.inputs = []
        self.keepDebugInfo = True
        # gcc-specific
        self.addressModel = None
        self.lto = None
        self.noUndefined = True
        # nvcc-specific

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        self.inputs.extend(project._inputs)
        self.inputs.extend(project._inputLibs)
        toolchain.emit_link(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


class CppProject(build.Project):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        self.outputPath = None
        self.toolchain = self.get_toolchain()
        self._inputs = []
        self._inputLibs = []
        self.linkLibraries = []


    @abstractmethod
    def get_toolchain(self):
        pass


    # add input to library or linker commandline

    def add_input(self, filePath):
        self._inputs.append(filePath)

    def add_input_lib(self, filePath):
        self._inputLibs.append(filePath)
    def add_input_libs(self, filePaths):
        self._inputLibs.extend(filePaths)

    def add_lib_dependency(self, project):
        self._inputLibs.extend(project.linkLibraries)
        self.add_runtime_dependency_project(project)


    # precompiled header

    # For convenience, you can disable PCH creation by setting reallyCreatePCH = False.
    # In that case, the source header will be force-included instead.  (and no other
    # modifications will be necessary to client code)
    def make_pch(self, sourcePath, reallyCreatePCH = True):
        sourcePath = os.path.normpath(sourcePath)
        if self.toolchain.supportsPCH and reallyCreatePCH:
            if os.path.isabs(sourcePath):
                outputPath = os.path.join(self.builtDir, os.path.basename(sourcePath) + self.toolchain.pchFileExt)
            else:
                outputPath = os.path.join(self.builtDir, sourcePath + self.toolchain.pchFileExt)
                sourcePath = os.path.join(self.projectDir, sourcePath)
            task = CppTask(self, sourcePath, outputPath, self.projectDir)
            task.createPCH = True
            self.set_cpp_compile_options(task)
            if isinstance(self.toolchain, pynja.MsvcToolChain):
                self.add_input(outputPath + self.toolchain.objectFileExt)
            return task
        else:
            if not os.path.isabs(sourcePath):
                sourcePath = os.path.join(self.projectDir, sourcePath)
            task = DummyPchTask(self, sourcePath, self.projectDir)
            return task


    # C++ compile

    def cpp_compile_one(self, sourcePath):
        sourcePath = os.path.normpath(sourcePath)
        if os.path.isabs(sourcePath):
            outputPath = os.path.join(self.builtDir, os.path.basename(sourcePath) + self.toolchain.objectFileExt)
        else:
            outputPath = os.path.join(self.builtDir, sourcePath + self.toolchain.objectFileExt)
            sourcePath = os.path.join(self.projectDir, sourcePath)
        task = CppTask(self, sourcePath, outputPath, self.projectDir)
        self.set_cpp_compile_options(task)
        self.add_input(outputPath)
        return task

    def cpp_compile(self, filePaths):
        taskList = []
        for filePath in filePaths:
            task = self.cpp_compile_one(filePath)
            taskList.append(task)
        tasks = pynja.BuildTasks(taskList)
        return tasks

    def set_cpp_compile_options(self, task):
        """Can be overridden to apply common compiler options to CppTask created by cpp_compile*."""
        pass


    # static lib creation

    def make_static_lib(self, outputPath):
        if self.outputPath:
            raise Exception("outputPath already selected: " + self.outputPath)
        self.outputPath = outputPath
        self.libraryPath = outputPath
        self.linkLibraries.append(self.libraryPath)
        self.linkLibraries.extend(self._inputLibs)

        task = StaticLibTask(self, self.outputPath, self.projectDir)
        self.set_static_lib_options(task)
        return task

    def set_static_lib_options(self, task):
        """Can be overridden to apply options to StaticLibTask created by make_static_lib."""
        pass


    # shared lib creation

    def make_shared_lib(self, outputPath, libraryPath):
        if self.outputPath:
            raise Exception("outputPath already selected: " + self.outputPath)
        self.outputPath = outputPath
        self.libraryPath = libraryPath
        self.linkLibraries.append(self.libraryPath)
        self.add_runtime_dependency(self.outputPath)

        task = LinkTask(self, self.outputPath, self.projectDir)
        task.outputLibraryPath = libraryPath
        task.makeExecutable = False
        self.set_shared_lib_options(task)
        return task

    def set_shared_lib_options(self, task):
        """Can be overridden to apply options to LinkTask created by make_shared_lib."""
        pass


    # executable creation

    def make_executable(self, outputPath):
        if self.outputPath:
            raise Exception("outputPath already selected: " + self.outputPath)
        self.outputPath = outputPath
        self.add_runtime_dependency(self.outputPath)

        task = LinkTask(self, self.outputPath, self.projectDir)
        task.makeExecutable = True
        self.set_executable_options(task)
        return task

    def set_executable_options(self, task):
        """Can be overridden to apply options to LinkTask created by make_executable."""
        pass

