from abc import *
import os
import pynja.build


class CppTask(pynja.build.BuildTask):
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
        # gcc-specific
        self.addressModel = None # = {"-m32", "-m64"}
        # msvc-specific
        self.dynamicCRT = True
        self.minimalRebuild = False
        # nvcc-specific
        self.relocatableDeviceCode = True
        self.deviceDebugLevel = 1 # {0 = none, 1 = lineinfo, 2 = full [disables optimization]}

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        toolchain.emit_cpp_compile(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


class StaticLibTask(pynja.build.BuildTask):
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


class LinkTask(pynja.build.BuildTask):
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
        # nvcc-specific

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        self.inputs.extend(project._inputs)
        toolchain.emit_link(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


class CppProject(pynja.build.Project):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        self.outputPath = None
        self.toolchain = self.get_toolchain()
        self._inputs = []

    @abstractmethod
    def get_toolchain(self):
        pass

    @abstractmethod
    def emit(self):
        pass


    # add input to library or linker commandline

    def add_input(self, filePath):
        self._inputs.append(filePath)

    def add_input_lib(self, filePath):
        return self.add_input(filePath)


    # C++ compile

    def cpp_compile_one(self, sourcePath):
        outputPath = None
        if os.path.isabs(sourcePath):
            outputPath = os.path.join(self.builtDir, os.basename(sourcePath) + self.toolchain.objectFileExt)
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
        tasks = pynja.build.BuildTasks(taskList)
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

        task = LinkTask(self, self.outputPath, self.projectDir)
        task.makeExecutable = True
        self.set_executable_options(task)
        return task

    def set_executable_options(self, task):
        """Can be overridden to apply options to LinkTask created by make_executable."""
        pass

