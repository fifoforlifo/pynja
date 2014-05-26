import os
from .tc import *
from . import build


class Re2cTask(build.BuildTask):
    def __init__(self, project, sourcePath, builtDir, workingDir, toolchain, outputExt='.cpp'):
        super().__init__(project)
        self.sourcePath = sourcePath
        self.builtDir = builtDir
        self.workingDir = workingDir
        self.toolchain = toolchain
        # commandline options
        self.useBitVectors = True           # -b
        #self.conditionSupport = False       # -c
        self.debug = False                  # -d
        self.emitDot = False                # -D
        self.storableState = False          # -f
        self.flexSyntax = False             # -F
        self.computedGoto = False           # -g
        self.lineMappings = True            # -i when False
        self.reuse = False                  # -r
        self.nestedIfs = False              # -s
        #self.flexHeader = False             # -t
        self.charType = 'ascii'             # valid options are { 'ascii', 'ucs2', 'utf32' }
                                            # for                           -w      -u
        self.singlePass = False             # -1

        self._calc_output(outputExt)

    def emit(self):
        project = self.project
        toolchain = self.toolchain
        toolchain.emit_build(project, self)
        if self.phonyTarget:
            project.projectMan.add_phony_target(self.phonyTarget, self.outputPath)

    def _calc_output(self, outputExt):
        sourcePath = os.path.normpath(self.sourcePath).replace("\\", "/")
        basename = os.path.basename(sourcePath)
        if os.path.isabs(sourcePath):
            self.sourcePath = sourcePath
            self.outputPath = os.path.join(self.builtDir, basename + outputExt)
        else:
            self.sourcePath = os.path.join(self.workingDir, sourcePath).replace("\\", "/")
            self.outputPath = os.path.join(self.builtDir, os.path.dirname(sourcePath), basename + outputExt)


class Re2cToolChain(build.ToolChain):
    """re2c lexer generator driver."""

    def __init__(self, re2cPath):
        super().__init__("re2c")
        self._re2cPath = re2cPath

    def emit_rules(self, ninjaFile):
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# re2c\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule re2c\n")
        ninjaFile.write("  depfile = $DEP_FILE\n")
        ninjaFile.write("  command = \"%s\"  -$OPTIONS -o \"$OUT_FILE\"  \"$SRC_FILE\" \n" % (self._re2cPath))
        ninjaFile.write("  description = re2c $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")

    def emit_build(self, project, task):
        options = []
        if task.useBitVectors:
            options.append("s")
        if task.debug:
            options.append("d")
        if task.emitDot:
            options.append("D")
        if task.storableState:
            options.append("f")
        if task.flexSyntax:
            options.append("F")
        if task.computedGoto:
            options.append("g")
        if not task.lineMappings:
            options.append("i")
        if task.reuse:
            options.append("r")
        if task.nestedIfs:
            options.append("s")
        if task.singlePass:
            options.append("1")

        if task.charType == 'ucs2':
            options.append("w")
        elif task.charType == 'utf32':
            options.append("u")
        else: # catch-all, handles default behavior of task.charType == 'ascii':
            pass

        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        outputPath = build.ninja_esc_path(task.outputPath)
        sourcePath = build.ninja_esc_path(task.sourcePath)
        re2cPath   = build.ninja_esc_path(self._re2cPath)
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        optionsStr = "".join(options)
        extraOutputs = " ".join([build.ninja_esc_path(p) for p in task.extraOutputs])

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s : re2c  %(sourcePath)s | %(re2cPath)s" % locals())
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  SRC_FILE    = %s\n" % task.sourcePath)
        ninjaFile.write("  OUT_FILE    = %s\n" % task.outputPath)
        ninjaFile.write("  OPTIONS     = %s\n" % optionsStr)
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")
