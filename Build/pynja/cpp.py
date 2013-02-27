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

    def emit(self):
        pass


class CppProject(pynja.build.Project):
    def __init__(self, projectMan, variant):
        super().__init__(self, projectMan, variant)
        self._inputs = []

    # add input to library or linker output
    def add_input(self, filePath):
        self._inputs.append(filePath)
    def add_input_lib(self, filePath):
        return self.add_input(filePath)

    def cpp_compile_one(self, sourcePath):
        outputPath = None
        if os.path.isabs(sourcePath):
            outputPath = os.path.join(self.get_built_dir(), os.basename(sourcePath))
        else:
            outputPath = os.path.join(self.get_built_dir(), sourcePath + ".o")
        task = CppTask(self, sourcePath, outputPath, get_project_dir())
        return task
    def cpp_compile(self, filePaths):
        taskList = []
        for filePath in filePaths:
            task = self.cpp_compile_one(filePath)
            taskList.append(task)
        tasks = pynja.build.BuildTasks(taskList)
        return tasks
    def set_compile_options(self, task):
        pass

    def make_static_lib(self, name):
        pass

    def set_static_lib_options(self, task):
        pass

    def link_shared_lib(self, name):
        pass
    def link_executable(self, arg1):
        pass

    def set_link_options(self, task):
        pass

    def emit(self):
        pass

