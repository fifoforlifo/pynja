import os
from abc import *
from . import build


class JavaTask(build.BuildTask):
    # outputPath = fanin file
    def __init__(self, project, workingDir, outputPath, outputDir):
        super().__init__(project)
        self.sourceFilePaths = []
        self.workingDir = workingDir
        self.outputPath = outputPath
        self.outputDir = outputDir
        self.classPaths = []
        self.verbose = False

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        toolchain.emit_java_compile(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


class JarTask(build.BuildTask):
    def __init__(self, project, workingDir, outputPath):
        super().__init__(project)
        self.workingDir = workingDir
        self.outputPath = outputPath

    def emit(self):
        project = self.project
        toolchain = project.toolchain
        toolchain.emit_jar_create(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)


class JavaProject(build.Project):
    def __init__(self, projectMan, variant):
        super().__init__(projectMan, variant)
        self.faninPath = os.path.join(self.builtDir, "java_compile.fanin")
        self.outputPath = None
        self.outputDir = os.path.join(self.builtDir, "classes")
        self.toolchain = self.get_toolchain()
        self.classPaths = []
        self.extraDepsForJar = []

    def get_java_project(self, projectName, variant):
        project = self.projectMan.get_project(projectName, self.variant)
        self.extraDepsForJar.append(project.faninPath)
        if project.outputPath:
            self.classPaths.append(project.outputPath)
        return project

    def java_compile(self, sourceFilePaths, classPaths = None):
        task = JavaTask(self, self.projectDir, self.faninPath, self.outputDir)
        task.sourceFilePaths.extend(sourceFilePaths)
        if classPaths:
            task.classPaths.extend(classPaths)
        task.classPaths.extend(self.classPaths)
        self.set_java_compile_options(task)
        return task

    def set_java_compile_options(self, task):
        pass

    def jar_create(self, jarFileName):
        if self.outputPath:
            raise Exception("outputPath already set for this project")
        self.outputPath = os.path.join(self.builtDir, jarFileName)
        task = JarTask(self, os.path.join(self.builtDir, "classes"), self.outputPath)
        task.extraDeps.append(self.faninPath)
        for extraDep in self.extraDepsForJar:
            task.extraDeps.append(extraDep)
        return task

