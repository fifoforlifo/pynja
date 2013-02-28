import os
import pynja.build


def write_rsp_file(project, task, options):
    rspContents = ' '.join(options)
    rspPath = task.outputPath + ".rsp"
    pynja.build.write_file_if_different(rspPath, rspContents)

    project.makeFiles.append(rspPath)


class GccToolChain(pynja.build.ToolChain):
    """A toolchain object capable of driving gcc and mingw"""

    def __init__(self, name, installDir, prefix = None, suffix = None):
        super().__init__(name)
        self.installDir = installDir
        self.prefix = prefix
        self.suffix = suffix
        self._scriptDir = os.path.join(os.path.dirname(__file__), "gcc")
        self._cxx_script  = os.path.join(self._scriptDir, "gcc-cxx-invoke.py")
        self._lib_script  = os.path.join(self._scriptDir, "gcc-lib-invoke.py")
        self._link_script = os.path.join(self._scriptDir, "gcc-link-invoke.py")
        pass

    pass


if os.name == "nt":
    # define MSVC toolchain

    class MsvcToolChain(pynja.build.ToolChain):
        """A toolchain object capable of driving msvc 8.0 and greater."""

        def __init__(self, name, installDir, arch):
            super().__init__(name)
            self.installDir = installDir
            self.arch = arch
            self._scriptDir = os.path.join(os.path.dirname(__file__), "msvc")
            self._cxx_script  = os.path.join(self._scriptDir, "msvc-cxx-invoke.py")
            self._lib_script  = os.path.join(self._scriptDir, "msvc-lib-invoke.py")
            self._link_script = os.path.join(self._scriptDir, "msvc-link-invoke.py")

        def emit_rules(self, ninjaFile):
            ninjaFile.write("#############################################\n")
            ninjaFile.write("# %s\n" % self.name)
            ninjaFile.write("\n")
            ninjaFile.write("rule %s_cxx\n" % self.name)
            ninjaFile.write("  depfile = $DEP_FILE\n")
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OBJ_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._cxx_script, self.installDir, self.arch))
            ninjaFile.write("  description = %s_cxx  $DESC\n" % self.name)
            ninjaFile.write("  restat = 1\n")
            ninjaFile.write("\n")
            ninjaFile.write("rule %s_lib\n" % self.name)
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._lib_script, self.installDir, self.arch))
            ninjaFile.write("  description = %s_lib  $DESC\n" % self.name)
            ninjaFile.write("  restat = 1\n")
            ninjaFile.write("\n")
            ninjaFile.write("rule %s_link\n" % self.name)
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._link_script, self.installDir, self.arch))
            ninjaFile.write("  description = %s_link $DESC\n" % self.name)
            ninjaFile.write("  restat = 1\n")
            ninjaFile.write("\n")


        def translate_opt_level(self, options, task):
            if task.optLevel == 0:
                options.append("/Od") # optimizations disabled
            elif 1 <= task.optLevel and task.optLevel <= 2:
                options.append("/O" + str(task.optLevel))
            elif task.optLevel == 3:
                options.append("/Ox")
            else:
                raise Exception("invalid optimization level: " + str(task.optLevel))

        def translate_debug_level(self, options, task):
            if not (0 <= task.debugLevel and task.debugLevel <= 3):
                raise Exception("invalid debug level: " + str(task.debugLevel))

            if task.debugLevel == 0:
                return

            if task.debugLevel == 1:
                options.append("/Zd")
            elif task.debugLevel == 2:
                options.append("/Zi")
            elif task.debugLevel == 3:
                options.append("/ZI")

            # rename PDB file
            options.append("\"/Fd%s.pdb\"" % task.outputPath)

            if task.minimalRebuild:
                options.append("/Gm")

        def translate_include_paths(self, options, task):
            for includePath in task.includePaths:
                if not includePath:
                    raise Exception("empty includePath set for: " + task.outputPath)
                options.append("/I\"%s\"" % includePath)

        def translate_defines(self, options, task):
            for define in task.defines:
                if not define:
                    raise Exception("empty define set for: " + task.outputPath)
                options.append("/D\"%s\"" % define)

        def translate_crt(self, options, task):
            if task.optLevel == 0:
                if task.dynamicCRT:
                    options.append("/MDd")
                else:
                    options.append("/MTd")
            else: # it's an optimized build
                if task.dynamicCRT:
                    options.append("/MD")
                else:
                    options.append("/MT")


        def emit_cpp_compile(self, project, task):
            ninjaFile = project.projectMan.ninjaFile
            name = self.name
            outputPath = pynja.build.ninja_esc_path(task.outputPath)
            sourcePath = pynja.build.ninja_esc_path(task.sourcePath)
            logPath = outputPath + ".log"
            sourceName = os.path.basename(task.sourcePath)
            outputName = os.path.basename(task.outputPath)
            scriptPath = pynja.build.ninja_esc_path(self._cxx_script)
            debugOutputs = ""
            if task.debugLevel >= 1:
                debugOutputs = debugOutputs + " " + outputPath + ".pdb"
                if task.minimalRebuild:
                    debugOutputs = debugOutputs + " " + outputPath + ".idb"

            # write build command
            ninjaFile.write("build %(outputPath)s %(debugOutputs)s %(logPath)s : %(name)s_cxx  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s" % locals())
            pynja.build.translate_extra_deps(ninjaFile, task, False)
            pynja.build.translate_order_only_deps(ninjaFile, task, True)
            ninjaFile.write("\n")

            ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
            ninjaFile.write("  SRC_FILE    = %s\n" % task.sourcePath)
            ninjaFile.write("  OBJ_FILE    = %s\n" % task.outputPath)
            ninjaFile.write("  DEP_FILE    = %s.d\n" % task.outputPath)
            ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
            ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
            ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
            ninjaFile.write("\n")

            # write response file
            options = []
            options.append("/nologo")
            options.append("/c")
            # translate simple options first for ease of viewing
            self.translate_opt_level(options, task)
            self.translate_debug_level(options, task)
            self.translate_crt(options, task)
            self.translate_include_paths(options, task)
            self.translate_defines(options, task)
            options.extend(task.extraOptions)
            write_rsp_file(project, task, options)

        def emit_static_lib(self, project, task):
            ninjaFile = project.projectMan.ninjaFile
            name = self.name
            outputPath = pynja.build.ninja_esc_path(task.outputPath)
            logPath = outputPath + ".log"
            outputName = os.path.basename(task.outputPath)
            scriptPath = pynja.build.ninja_esc_path(self._lib_script)

            ninjaFile.write("build %(outputPath)s %(logPath)s : %(name)s_lib | %(outputPath)s.rsp %(scriptPath)s" % locals())
            pynja.build.translate_path_list(ninjaFile, task.inputs)
            pynja.build.translate_extra_deps(ninjaFile, task, False)
            pynja.build.translate_order_only_deps(ninjaFile, task, True)
            ninjaFile.write("\n")

            ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
            ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
            ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
            ninjaFile.write("  DESC        = %s\n" % outputName)
            ninjaFile.write("\n")
            ninjaFile.write("\n")

            # write response file
            options = []
            options.append("/nologo")
            options.append("\"/OUT:%s\"" % task.outputPath)
            for input in task.inputs:
                options.append("\"%s\"" % input)
            write_rsp_file(project, task, options)

        def emit_link(self, project, task):
            ninjaFile = project.projectMan.ninjaFile
            name = self.name
            outputPath = pynja.build.ninja_esc_path(task.outputPath)
            libraryPath = ""
            if task.outputLibraryPath and (task.outputLibraryPath != task.outputPath):
                libraryPath = pynja.build.ninja_esc_path(task.outputLibraryPath)
            logPath = outputPath + ".log"
            outputName = os.path.basename(task.outputPath)
            scriptPath = pynja.build.ninja_esc_path(self._lib_script)

            ninjaFile.write("build %(outputPath)s %(libraryPath)s %(logPath)s : %(name)s_link | %(outputPath)s.rsp %(scriptPath)s" % locals())
            for input in task.inputs:
                if os.path.isabs(input):
                    inputEsc = pynja.build.ninja_esc_path(input)
                    ninjaFile.write(" ")
                    ninjaFile.write(inputEsc)
            pynja.build.translate_extra_deps(ninjaFile, task, False)
            pynja.build.translate_order_only_deps(ninjaFile, task, True)
            ninjaFile.write("\n")

            ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
            ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
            ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
            ninjaFile.write("  DESC        = %s\n" % outputName)
            ninjaFile.write("\n")
            ninjaFile.write("\n")

            # write response file
            options = []
            options.append("/nologo")
            if not task.makeExecutable:
                options.append("/DLL")
            options.append("\"/OUT:%s\"" % task.outputPath)
            if task.keepDebugInfo:
                options.append("/DEBUG")
            for input in task.inputs:
                options.append("\"%s\"" % input)
            options.extend(task.extraOptions)
            write_rsp_file(project, task, options)
