import os
from .tc import *
from . import build
from . import monkey

class ProtocTask(build.BuildTask):
    def __init__(self, project, sourcePath, builtDir, workingDir, language, toolchain):
        super().__init__(project)
        self.sourcePath = sourcePath
        self.builtDir = builtDir
        self.workingDir = workingDir
        self.toolchain = toolchain
        self.outputLanguage = language # one of {'cpp', 'java', 'python'}
        # common compiler options
        self.includePaths = []
        self.includeImports = False
        self.errorFormatMsvs = True

        self._calc_output()

    def emit(self):
        project = self.project
        toolchain = self.toolchain
        toolchain.emit_build(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)

    def _calc_output(task):
        sourcePath = os.path.normpath(task.sourcePath)
        (bareName, ext) = os.path.splitext(os.path.basename(sourcePath))
        if os.path.isabs(sourcePath):
            basePath = os.path.join(task.builtDir, bareName)
            task.sourcePath = sourcePath
        else:
            basePath = os.path.join(task.builtDir, os.path.dirname(sourcePath), bareName)
            task.sourcePath = os.path.join(task.workingDir, sourcePath)
        if task.outputLanguage == 'cpp':
            task.outputPath = basePath + ".pb.cc"
            task.outputHeader = basePath + ".pb.h"
            task.extraOutputs.append(task.outputHeader)
        else:
            raise Exception("unknown language %s" % task.outputLanguage)


class ProtocToolChain(build.ToolChain):
    """Protocol buffer compiler driver."""

    def __init__(self, protocPath):
        super().__init__("protoc")
        self.protocPath = protocPath
        self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
        self._protocScript = os.path.join(self._scriptDir, "protoc-invoke.py")

    def emit_rules(self, ninjaFile):
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# protoc\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule protoc\n")
        ninjaFile.write("  depfile = $DEP_FILE\n")
        ninjaFile.write("  command = python \"%s\"  \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OUT_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"$RSP_FILE\"\n" % (self._protocScript, self.protocPath))
        ninjaFile.write("  description = protoc $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")

    def emit_build(self, project, task):
        # write response file
        options = []
        # include paths placed first, and delimited with "|||", to make protoc-invoke.py easier to write
        options.append("-I\"%s\"" % os.path.dirname(task.sourcePath))
        for includePath in task.includePaths:
            options.append("-I\"%s\"" % includePath)
        options.append("|||")
        options.append("--%s_out=\"%s\"" % (task.outputLanguage, os.path.dirname(task.outputPath)))
        if task.includeImports:
            options.append("--include_imports")
        if task.errorFormatMsvs:
            options.append("--error_format=msvs")
        write_rsp_file(project, task, options)

        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        outputPath = build.xlat_path(project, task.outputPath)
        sourcePath = build.xlat_path(project, task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._protocScript)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : protoc  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s" % locals())
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
        ninjaFile.write("  SRC_FILE    = %s\n" % sourcePath)
        ninjaFile.write("  OUT_FILE    = %s\n" % outputPath)
        ninjaFile.write("  DEP_FILE    = %s.d\n" % outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % outputPath)
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")

def add_tool(cls):
    def _protoc_one(self, sourcePath, language):
        protocToolChain = self.projectMan.get_toolchain("protoc")
        task = ProtocTask(self, sourcePath, self.builtDir, self.projectDir, language, protocToolChain)
        self.set_protoc_options(task)
        self._forcedDeps.add(task.outputHeader)
        return task

    @monkey.new_method(cls)
    def protoc(self, filePaths, language):
        if isinstance(filePaths, str):
            return _protoc_one(self, filePaths, language)
        else:
            taskList = []
            for filePath in filePaths:
                task = _protoc_one(self, filePath, language)
                taskList.append(task)
            tasks = build.BuildTasks(taskList)
            return tasks

    @monkey.new_method(cls)
    def protoc_cpp_compile(self, filePaths):
        proto_sources = []
        with self.protoc(filePaths, 'cpp') as tasks:
            for task in tasks:
                proto_sources.append(task.outputPath)
            self.cpp_compile(proto_sources)
        return proto_sources

    @monkey.new_method(cls)
    def set_protoc_options(self, task):
        pass
