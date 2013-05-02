import os
from .tc import *
from . import build


class JavacToolChain(build.ToolChain):
    """A toolchain object capable of driving the Oracle/Sun jdk."""

    def __init__(self, name, jdkDir):
        super().__init__(name)
        self.jdkDir = jdkDir
        self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
        self._javac_script = os.path.join(self._scriptDir, "javac-invoke.py")
        self._jar_script = os.path.join(self._scriptDir, "jar-invoke.py")

    def emit_rules(self, ninjaFile):
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# %s\n" % self.name)
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_javac\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  compile  \"$WORKING_DIR\"  \"%s\"  \"$OUT_DIR\"  \"$OPTIONS\"  \"$CLASSPATHS\"  \"$SOURCES\"  \"$LOG_FILE\"  \"$LIST_FILE\"  \"$FANIN_FILE\"  \n" % (self._javac_script, self.jdkDir))
        ninjaFile.write("  description = %s  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_javac_fanin\n" % self.name)
        ninjaFile.write("  depfile = $DEP_FILE\n")
        ninjaFile.write("  command = python \"%s\"  fanin  \"$WORKING_DIR\"  \"%s\"  \"$OUT_DIR\"  \"$OPTIONS\"  \"$CLASSPATHS\"  \"$SOURCES\"  \"$LOG_FILE\"  \"$LIST_FILE\"  \"$FANIN_FILE\"  \n" % (self._javac_script, self.jdkDir))
        ninjaFile.write("  description = %s  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")

        ninjaFile.write("rule %s_jar\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"%s\"  \"$OUTPUT_FILE\"  \"$LOG_FILE\"  \n" % (self._jar_script, self.jdkDir))
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("  description = %s  $DESC\n" % self.name)
        ninjaFile.write("\n")

    def emit_java_compile(self, project, task):
        # write options file; this also updates extraInputs/extraOutputs
        options = []
        if task.verbose:
            options.append("-verbose")
        write_rsp_file(project, task, options)
        write_rsp_file(project, task, task.classPaths, task.outputPath + ".cp", "\n")
        write_rsp_file(project, task, task.sourceFilePaths, task.outputPath + ".src", "\n")
        for classPath in task.classPaths:
            if classPath.endswith(".jar"):
                task.extraDeps.append(classPath)


        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = build.ninja_esc_path(task.outputPath)
        outputName = os.path.basename(outputPath)
        scriptPath = build.ninja_esc_path(self._javac_script)

        extraOutputs = " ".join([build.ninja_esc_path(p) for p in task.extraOutputs])

        # write build command
        ninjaFile.write("build %(outputPath)s.list %(extraOutputs)s %(outputPath)s.log : %(name)s_javac | %(outputPath)s.rsp %(outputPath)s.cp %(outputPath)s.src  %(scriptPath)s " % locals())
        absSourceFilePaths = [os.path.join(task.workingDir, p) for p in task.sourceFilePaths]
        build.translate_path_list(ninjaFile, absSourceFilePaths)
        build.translate_extra_deps(ninjaFile, task, False)
        build.translate_order_only_deps(ninjaFile, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  OUT_DIR     = %s\n" % task.outputDir)
        ninjaFile.write("  OPTIONS     = %s.rsp\n" % task.outputPath)
        ninjaFile.write("  CLASSPATHS  = %s.cp\n" % task.outputPath)
        ninjaFile.write("  SOURCES     = %s.src\n" % task.outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  LIST_FILE   = %s.list\n" % task.outputPath)
        ninjaFile.write("  FANIN_FILE  = %s\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % (outputName))
        ninjaFile.write("\n")

        # write fanin command
        ninjaFile.write("build %(outputPath)s : %(name)s_javac_fanin | %(outputPath)s.list %(scriptPath)s \n" % locals())
        ninjaFile.write("  DEP_FILE    = %s.d\n" % task.outputPath)
        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  OUT_DIR     = %s\n" % task.outputDir)
        ninjaFile.write("  OPTIONS     = %s.rsp\n" % task.outputPath)
        ninjaFile.write("  CLASSPATHS  = %s.cp\n" % task.outputPath)
        ninjaFile.write("  SOURCES     = %s.src\n" % task.outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  LIST_FILE   = %s.list\n" % task.outputPath)
        ninjaFile.write("  FANIN_FILE  = %s\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % (outputName))
        ninjaFile.write("\n")

    def emit_jar_create(self, project, task):
        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = build.ninja_esc_path(task.outputPath)
        outputName = os.path.basename(outputPath)
        scriptPath = build.ninja_esc_path(self._jar_script)

        extraOutputs = " ".join([build.ninja_esc_path(p) for p in task.extraOutputs])

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(outputPath)s.log : %(name)s_jar | %(scriptPath)s " % locals())
        build.translate_extra_deps(ninjaFile, task, False)
        build.translate_order_only_deps(ninjaFile, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  OUTPUT_FILE = %s\n" % task.outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % (task.outputPath))
        ninjaFile.write("\n")
