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
        self.debugLevel = 3
        self.optLevel = 3
        self.includePaths = []
        self.defines = []
        # gcc-specific
        self.addressModel = None
        # msvc-specific
        self.crt = "dynamic"
        self.minimalRebuild = False

    def emit(self):
        pass


class StaticLibTask(pynja.build.BuildTask):
    def __init__(self, project, outputPath, workingDir):
        super().__init__(project)
        self.outputPath = outputPath
        self.workingDir = workingDir

    def emit(self):
        pass


class LinkTask(pynja.build.BuildTask):
    def __init__(self, project, outputPath, workingDir):
        super().__init__(project)
        self.outputPath = outputPath
        self.workingDir = workingDir
        self.makeExecutable = True # if False, make shared library instead
        self.inputs = []

    def emit(self):
        pass


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
            outputPath = os.path.join(self.builtDir, os.basename(sourcePath) + ".o")
        else:
            outputPath = os.path.join(self.builtDir, sourcePath + ".o")
            sourcePath = os.path.join(self.projectDir, sourcePath)
        task = CppTask(self, sourcePath, outputPath, self.projectDir)
        self.set_cpp_compile_options(task)
        self.add_input(outputPath)
        print(outputPath)
        return task

    def cpp_compile(self, filePaths):
        taskList = []
        for filePath in filePaths:
            task = self.cpp_compile_one(filePath)
            taskList.append(task)
        tasks = pynja.build.BuildTasks(taskList)
        return tasks

    def set_cpp_compile_options(self, task):
        """Can be overridden to apply common compiler options to all cpp_compiles."""
        pass


    # static lib creation

    def make_static_lib(self, outputPath):
        if self.outputPath:
            raise Exception("outputPath already selected: " + self.outputPath)
        self.outputPath = outputPath
        self.libraryPath = outputPath

        task = StaticLibTask(self, self.outputPath, self.projectDir)
        self.set_static_lib_options(task)
        print(self.outputPath)
        return task

    def set_static_lib_options(self, task):
        """Can be overridden to apply options to StaticLibTask."""
        pass


    # shared lib creation

    def make_shared_lib(self, outputPath, libraryPath):
        if self.outputPath:
            raise Exception("outputPath already selected: " + self.outputPath)
        self.outputPath = outputPath
        self.libraryPath = libraryPath

        task = LinkTask(self, self.outputPath, self.projectDir)
        task.makeExecutable = False
        self.set_shared_lib_options(task)
        print(self.outputPath)
        return task

    def set_shared_lib_options(self, task):
        """Can be overridden to apply options to LinkTask."""
        pass


    # executable creation

    def make_executable(self, outputPath):
        if self.outputPath:
            raise Exception("outputPath already selected: " + self.outputPath)
        self.outputPath = outputPath

        task = LinkTask(self, self.outputPath, self.projectDir)
        task.makeExecutable = True
        self.set_executable_options(task)
        print(self.outputPath)
        return task

    def set_executable_options(self, task):
        """Can be overridden to apply options to LinkTask."""
        pass

