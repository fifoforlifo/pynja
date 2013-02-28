import os
import pynja.build

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
            ninjaFile.write("#############################################\n");
            ninjaFile.write("# %s\n" % self.name);
            ninjaFile.write("\n");
            ninjaFile.write("rule %s_cxx\n" % self.name);
            ninjaFile.write("  depfile = $DEP_FILE\n");
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OBJ_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._cxx_script, self.installDir, self.arch));
            ninjaFile.write("  description = %s_cxx  $DESC\n" % self.name);
            ninjaFile.write("  restat = 1\n");
            ninjaFile.write("\n");
            ninjaFile.write("rule %s_lib\n" % self.name);
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._lib_script, self.installDir, self.arch));
            ninjaFile.write("  description = %s_lib  $DESC\n" % self.name);
            ninjaFile.write("  restat = 1\n");
            ninjaFile.write("\n");
            ninjaFile.write("rule %s_link\n" % self.name);
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._link_script, self.installDir, self.arch));
            ninjaFile.write("  description = %s_link $DESC\n" % self.name);
            ninjaFile.write("  restat = 1\n");
            ninjaFile.write("\n");


        def translate_opt_level(self, task, options):
            if task.optLevel == 0:
                options.append("/Od"); # optimizations disabled
            elif 1 <= task.optLevel and task.optLevel <= 2:
                options.append("/O" + str(task.optLevel))
            elif task.optLevel == 3:
                options.append("/Ox")
            else:
                raise Exception("invalid optimization level: " + str(task.optLevel))

        def translate_debug_level(self, task, options):
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

        def translate_include_paths(self, task, options):
            for includePath in task.includePaths:
                if not includePath:
                    raise Exception("empty includePath set for: " + task.outputPath)
                options.append("/I\"%s\"" % includePath)

        def translate_defines(self, task, options):
            for define in task.defines:
                if not define:
                    raise Exception("empty define set for: " + task.outputPath)
                options.append("/D\"%s\"" % define)

        def translate_crt(self, task, options):
            if task.optLevel == 0:
                if task.dynamicCrt:
                    options.append("/MDd")
                else:
                    options.append("/MTd")
            else: # it's an optimized build
                if task.dynamicCrt:
                    options.append("/MD")
                else:
                    options.append("/MT")


        def emit_cpp_compile(self, project, task):
            pass

        def emit_static_lib(self, project, task):
            pass

        def emit_link(self, project, task):
            pass
