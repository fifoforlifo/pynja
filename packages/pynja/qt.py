import os
from .tc import *
from . import build


class QtUiTask(build.BuildTask):
    def __init__(self, project, sourcePath, outputPath, workingDir, toolchain):
        super().__init__(project)
        self.sourcePath = sourcePath
        self.outputPath = outputPath
        self.workingDir = workingDir
        self.toolchain = toolchain
        self.tr = None
        self.generateIncludeGuards = True

    def emit(self):
        project = self.project
        toolchain = self.toolchain
        toolchain.emit_uic(project, self)
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

    def emit_rules(self, ninjaFile):
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# Qt uic\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s\n" % self._uicRule)
        ninjaFile.write("  command = python \"%s\"  \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OUT_FILE\"  \"$LOG_FILE\"\n" % (self._uicScript, self.qtBinDir))
        ninjaFile.write("  description = uic $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")

    def emit_uic(self, project, task):
        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        outputPath = build.ninja_esc_path(task.outputPath)
        sourcePath = build.ninja_esc_path(task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._uicScript)

        extraOutputs = " ".join([build.ninja_esc_path(p) for p in task.extraOutputs])
        ruleName = self._uicRule

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(ruleName)s %(sourcePath)s | %(scriptPath)s" % locals())
        build.translate_extra_deps(ninjaFile, task, False)
        build.translate_order_only_deps(ninjaFile, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  SRC_FILE    = %s\n" % task.sourcePath)
        ninjaFile.write("  OUT_FILE    = %s\n" % task.outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")
