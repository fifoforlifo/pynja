import os
from .tc import *
from . import build
from . import monkey


class QtUiTask(build.BuildTask):
    def __init__(self, project, sourcePath, outputPath, workingDir, toolchain):
        super().__init__(project)
        self.sourcePath = sourcePath
        self.outputPath = outputPath
        self.workingDir = workingDir
        self.toolchain = toolchain

    def emit(self):
        project = self.project
        toolchain = self.toolchain
        toolchain.emit_uic(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)

class QtMocTask(build.BuildTask):
    def __init__(self, project, sourcePath, outputPath, workingDir, toolchain):
        super().__init__(project)
        self.sourcePath = sourcePath
        self.outputPath = outputPath
        self.workingDir = workingDir
        self.toolchain = toolchain
        self.includePaths = []
        self.defines = []
        self.emitInclude = True

    def emit(self):
        project = self.project
        toolchain = self.toolchain
        toolchain.emit_moc(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)

class QtToolChain(build.ToolChain):
    """Qt tools driver."""

    def __init__(self, name, qtBinDir):
        super().__init__(name)
        self.qtBinDir = qtBinDir
        self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
        self._uicScript = os.path.join(self._scriptDir, "qt-uic-invoke.py")
        self._uicRule = "%s_uic" % self.name
        self._mocScript = os.path.join(self._scriptDir, "qt-moc-invoke.py")
        self._mocRule = "%s_moc" % self.name

    def emit_rules(self, ninjaFile):
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# Qt uic\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s\n" % self._uicRule)
        ninjaFile.write("  command = python \"%s\"  \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OUT_FILE\"  \"$LOG_FILE\"\n" % (self._uicScript, self.qtBinDir))
        ninjaFile.write("  description = uic $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# Qt moc\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s\n" % self._mocRule)
        ninjaFile.write("  command = python \"%s\"  \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OUT_FILE\"  \"$LOG_FILE\"  \"$RSP_FILE\"\n" % (self._mocScript, self.qtBinDir))
        ninjaFile.write("  description = moc $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")

    def emit_uic(self, project, task):
        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        outputPath = build.xlat_path(project, task.outputPath)
        sourcePath = build.xlat_path(project, task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._uicScript)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])
        ruleName = self._uicRule

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(ruleName)s %(sourcePath)s | %(scriptPath)s" % locals())
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
        ninjaFile.write("  SRC_FILE    = %s\n" % sourcePath)
        ninjaFile.write("  OUT_FILE    = %s\n" % outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")

    def translate_include_paths(self, options, task):
        for includePath in task.includePaths:
            if not includePath:
                raise Exception("empty includePath set for: " + task.outputPath)
            options.append("-I\"%s\"" % includePath)

    def translate_defines(self, options, task):
        for define in task.defines:
            if not define:
                raise Exception("empty define set for: " + task.outputPath)
            options.append("-D%s" % define)

    def emit_moc(self, project, task):
        # write response file; this also updates extraInputs/extraOutputs
        options = []
        self.translate_include_paths(options, task)
        self.translate_defines(options, task)
        if not task.emitInclude:
            options.append("-i")
        write_rsp_file(project, task, options)

        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        outputPath = build.xlat_path(project, task.outputPath)
        sourcePath = build.xlat_path(project, task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._mocScript)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])
        ruleName = self._mocRule

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(ruleName)s  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s " % locals())
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
        ninjaFile.write("  SRC_FILE    = %s\n" % sourcePath)
        ninjaFile.write("  OUT_FILE    = %s\n" % outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % outputPath)
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")

def add_tool(cls):
    @monkey.new_method(cls)
    def qt_init(self, qtToolChainName, qtBuiltDir=None):
        self.qtToolChain = self.projectMan.get_toolchain('qt5vc11')
        self.qtBuiltDir = qtBuiltDir
        if not self.qtBuiltDir:
            self.qtBuiltDir = os.path.join(self.builtDir, "qt")
        self.qtIncludePaths = [
            os.path.normpath(os.path.join(self.qtToolChain.qtBinDir, "..", "include")),
            self.qtBuiltDir,
        ]
        self.qtLibDir = os.path.normpath(os.path.join(self.qtToolChain.qtBinDir, "..", "lib"))

    def _qt_uic_one(self, sourcePath):
        (barename, ext) = os.path.splitext(os.path.basename(sourcePath))
        outputPath = os.path.join(self.qtBuiltDir, "ui_" + barename + ".h")
        if not os.path.isabs(sourcePath):
            sourcePath = os.path.join(self.projectDir, sourcePath)
        task = QtUiTask(self, sourcePath, outputPath, self.projectDir, self.qtToolChain)
        self._forcedDeps.add(outputPath)
        return task

    @monkey.new_method(cls)
    def qt_uic(self, filePaths):
        with self.qt_uic_ex(filePaths) as tasks:
            pass
        return tasks

    @monkey.new_method(cls)
    def qt_uic_ex(self, filePaths):
        if isinstance(filePaths, str):
            return _qt_uic_one(self, filePaths)
        else:
            taskList = []
            for filePath in filePaths:
                task = _qt_uic_one(self, filePath)
                taskList.append(task)
            tasks = build.BuildTasks(taskList)
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
        task = QtMocTask(self, sourcePath, outputPath, self.projectDir, self.qtToolChain)
        if not isHeader:
            task.emitInclude = False
        self.set_qt_moc_options(task)
        if outputPath.endswith(".moc"):
            self._forcedDeps.add(outputPath)
        return task

    @monkey.new_method(cls)
    def qt_moc(self, filePaths):
        with self.qt_moc_ex(filePaths) as tasks:
            pass
        return tasks

    @monkey.new_method(cls)
    def qt_moc_ex(self, filePaths):
        if isinstance(filePaths, str):
            return _qt_moc_one(self, filePaths)
        else:
            taskList = []
            for filePath in filePaths:
                task = _qt_moc_one(self, filePath)
                taskList.append(task)
            tasks = build.BuildTasks(taskList)
            return tasks

    @monkey.new_method(cls)
    def qt_moc_cpp_compile(self, filePaths):
        tasks = self.qt_moc(filePaths)
        moc_includables = [] # by convention these files are *.moc, which are 'includable' in a cpp but not quite headers :)
        for task in tasks:
            basename = os.path.basename(task.outputPath)
            if basename.startswith("moc_"):
                self.cpp_compile(task.outputPath)
            else:
                moc_includables.append(task.outputPath)

    @monkey.new_method(cls)
    def set_qt_moc_options(self, task):
        """Can be overridden to apply common options to QtMocTask created by qt_moc*."""
        self.set_include_paths_and_defines(task)

