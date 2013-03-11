import os
import pynja.build


def write_rsp_file(project, task, options):
    rspContents = ' \n'.join(options)
    rspPath = task.outputPath + ".rsp"
    pynja.build.write_file_if_different(rspPath, rspContents)

    project.makeFiles.append(rspPath)

def binutils_esc_path(path):
    return path.replace("\\", "/")

def get_lib_name(path):
    if path.endswith(".a"):
        fname = os.path.basename(path)
        if fname.startswith("lib"):
            return fname[3:-2]
    return None


class GccToolChain(pynja.build.ToolChain):
    """A toolchain object capable of driving gcc commandlines."""

    def __init__(self, name, installDir, prefix = None, suffix = None):
        super().__init__(name)
        self.installDir = installDir
        self.prefix = prefix
        self.ccName = "gcc"
        self.suffix = suffix
        self.objectFileExt = ".o"
        self.pchFileExt = ".gch"
        self.supportsPCH = True
        self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
        self._cxx_script  = os.path.join(self._scriptDir, "gcc-cxx-invoke.py")
        self._lib_script  = os.path.join(self._scriptDir, "gcc-lib-invoke.py")
        self._link_script = os.path.join(self._scriptDir, "gcc-link-invoke.py")

    def emit_rules(self, ninjaFile):
        prefix = self.prefix if self.prefix else "_NO_PREFIX_"
        suffix = self.suffix if self.suffix else "_NO_SUFFIX_"

        executable = "%s%s%s" % (self.prefix or "", self.ccName, self.suffix or "")

        ninjaFile.write("#############################################\n")
        ninjaFile.write("# %s\n" % self.name)
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_cxx\n" % self.name)
        ninjaFile.write("  depfile = $DEP_FILE\n")
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OBJ_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"%s\"  %s \"$RSP_FILE\"\n" % (self._cxx_script, self.installDir, executable))
        ninjaFile.write("  description = %s_cxx  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_lib\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s %s  \"$RSP_FILE\"\n" % (self._lib_script, self.installDir, prefix, suffix))
        ninjaFile.write("  description = %s_lib  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_link\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s %s  \"$RSP_FILE\"\n" % (self._link_script, self.installDir, prefix, suffix))
        ninjaFile.write("  description = %s_link $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")


    def translate_debug_level(self, options, task):
        if not (0 <= task.debugLevel <= 3):
            raise Exception("debugLevel must be between 0-3.  debugLevel was set to %s" % str(task.debugLevel))
        options.append("-g%d" % task.debugLevel)

    def translate_opt_level(self, options, task):
        if not (0 <= task.optLevel <= 3):
            raise Exception("optLevel must be between 0-3.  optLevel was set to %s" % str(task.optLevel))
        options.append("-O%d" % task.optLevel)

    def translate_warn_level(self, options, task):
        if not (0 <= task.warnLevel <= 4):
            raise Exception("invalid warn level: " + str(task.warnLevel))

        if task.warnLevel == 0:
            options.append("-w")
        else:
            if task.warnLevel >= 1:
                options.append("-Wall")
            if task.warnLevel >= 2:
                options.append("-Wconversion")
            if task.warnLevel >= 3:
                options.append("-Wextra")
            if task.warnLevel == 4:
                options.append("-Wpedantic")

        if task.warningsAsErrors:
            options.append("-Werror")

    def translate_include_paths(self, options, task):
        for includePath in task.includePaths:
            if not includePath:
                raise Exception("empty includePath set for: " + task.outputPath)
            includePathEsc = binutils_esc_path(includePath)
            options.append("-I\"%s\"" % includePathEsc)

    def translate_defines(self, options, task):
        for define in task.defines:
            if not define:
                raise Exception("empty define set for: " + task.outputPath)
            options.append("-D%s" % define)

    def translate_linker_inputs(self, options, task):
        for input in task.inputs:
            libName = get_lib_name(input)
            if libName:
                libDir = os.path.dirname(input)
                libDirEsc = binutils_esc_path(libDir)
                options.append("-L\"%s\"" % libDirEsc)
                options.append("-l\"%s\"" % libName)
            else:
                inputEsc = binutils_esc_path(input)
                options.append("\"%s\"" % inputEsc)

    def translate_address_model(self, options, task):
        if task.addressModel:
            options.append(task.addressModel)

    # See http://gcc.gnu.org/onlinedocs/gcc/C-Dialect-Options.html#C-Dialect-Options
    def get_language_option(self, std):
        if  (   std == "c90"
            or  std == "c98"
            or  std == "iso9899:1990"
            or  std == "iso9899:199409"
            or  std == "c99"
            or  std == "c9x"
            or  std == "iso9899:1999"
            or  std == "iso9899:199x"
            or  std == "gnu90"
            or  std == "gnu89"
            or  std == "gnu99"
            or  std == "gnu9x"
            ):
            return "-x c-header"
        else:
            return "-x c++-header"

    # note: this should be called *before* adding additional force includes
    def translate_pch(self, options, task):
        if task.createPCH:
            options.append(self.get_language_option(task.std))
        if task.usePCH:
            if task.usePCH.endswith(".gch") or task.usePCH.endswith(".pch"):
                headerPathEsc = binutils_esc_path(task.usePCH)[:-4]
            else:
                headerPathEsc = binutils_esc_path(task.usePCH)
            options.append("-include \"%s\"" % headerPathEsc)
            options.append("-H")
            options.append("-Winvalid-pch")

    def translate_dialect(self, options, task):
        if task.std:
            options.append("-std %s" % task.std)


    def translate_cpp_options(self, options, task):
        # translate simple options first for ease of viewing
        self.translate_dialect(options, task)
        self.translate_opt_level(options, task)
        self.translate_debug_level(options, task)
        self.translate_warn_level(options, task)
        self.translate_address_model(options, task)
        self.translate_include_paths(options, task)
        self.translate_defines(options, task)
        self.translate_pch(options, task)
        options.extend(task.extraOptions)


    def emit_cpp_compile(self, project, task):
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = pynja.build.ninja_esc_path(task.outputPath)
        sourcePath = pynja.build.ninja_esc_path(task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = pynja.build.ninja_esc_path(self._cxx_script)
        pchPath = ""
        if task.usePCH:
            pchPath = pynja.build.ninja_esc_path(task.usePCH)

        # write build command
        ninjaFile.write("build %(outputPath)s %(logPath)s : %(name)s_cxx  %(sourcePath)s | %(outputPath)s.rsp %(pchPath)s %(scriptPath)s" % locals())
        pynja.build.translate_extra_deps(ninjaFile, task, False)
        ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
        pynja.build.translate_order_only_deps(ninjaFile, task, False)
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
        options.append("-c")
        self.translate_cpp_options(options, task)
        write_rsp_file(project, task, options)

        if task.createPCH:
            project.projectMan.emit_copy(task.sourcePath, task.outputPath[:-4])

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
        ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
        pynja.build.translate_order_only_deps(ninjaFile, task, False)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")

        # write response file
        options = []
        options.append("rc")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("\"%s\"" % outputFileEsc)
        self.translate_linker_inputs(options, task)
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
        ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
        pynja.build.translate_order_only_deps(ninjaFile, task, False)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")

        # write response file
        options = []
        if not task.makeExecutable:
            options.append("-shared")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("-o \"%s\"" % outputFileEsc)
        self.translate_address_model(options, task)
        if not task.keepDebugInfo:
            options.append("--strip-debug")
        self.translate_linker_inputs(options, task)
        options.extend(task.extraOptions)
        write_rsp_file(project, task, options)


class ClangToolChain(GccToolChain):
    def __init__(self, name, installDir, prefix = None, suffix = None):
        super().__init__(name, installDir, prefix, suffix)
        self.ccName = "clang"
        self.pchFileExt = ".pch"


class NvccToolChain(pynja.build.ToolChain):
    """A toolchain object capable of driving nvcc (CUDA compiler)."""

    # hostCompiler = {gcc, msvc}
    def __init__(self, name, installDir, hostCompiler, hostInstallDir, addressModel):
        super().__init__(name)
        self.installDir = installDir
        self.hostCompiler = hostCompiler
        self.hostInstallDir = hostInstallDir
        self.addressModel = addressModel
        if "msvc" in self.hostCompiler:
            self.objectFileExt = ".obj"
            self.pchFileExt = ".pch"
        else:
            self.objectFileExt = ".o"
            self.pchFileExt = ".gch"
        self.supportsPCH = False
        self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
        self._cxx_script  = os.path.join(self._scriptDir, "nvcc-cxx-invoke.py")
        self._invoke_script  = os.path.join(self._scriptDir, "nvcc-invoke.py")

    def emit_rules(self, ninjaFile):
        ninjaFile.write("#############################################\n")
        ninjaFile.write("# %s\n" % self.name)
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_cxx\n" % self.name)
        ninjaFile.write("  depfile = $DEP_FILE\n")
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OBJ_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"%s\"  %s  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._cxx_script, self.installDir, self.hostCompiler, self.hostInstallDir, self.addressModel))
        ninjaFile.write("  description = %s_cxx  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_invoke\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._invoke_script, self.installDir, self.hostCompiler, self.hostInstallDir, self.addressModel))
        ninjaFile.write("  description = $DESC\n")
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")


    def translate_debug_level(self, options, task):
        if not (0 <= task.debugLevel <= 3):
            raise Exception("debugLevel must be between 0-3.  debugLevel was set to %s" % str(task.debugLevel))
        if task.debugLevel > 0:
            options.append("--debug")

    def translate_warn_level(self, options, task):
        if not (0 <= task.warnLevel <= 4):
            raise Exception("invalid warn level: " + str(task.warnLevel))

        if task.warnLevel == 0:
            options.append("-w")
        else:
            hostOptions = []
            if "gcc" in self.hostCompiler:
                GccToolChain.translate_warn_level(self, hostOptions, task)
            elif "msvc" in self.hostCompiler:
                MsvcToolChain.translate_warn_level(self, hostOptions, task)
            else:
                raise Exception("invalid hostCompiler %s" % str(self.hostCompiler))
            for option in hostOptions:
                options.append("-Xcompiler %s" % option)

    def translate_address_model(self, options, task):
        options.append(self.addressModel)

    def translate_device_debug_level(self, options, task):
        if not (0 <= task.deviceDebugLevel <= 2):
            raise Exception("invalid deviceDebugLevel: %s" % task.deviceDebugLevel)

        if task.deviceDebugLevel == 0:
            return
        elif task.deviceDebugLevel == 1:
            options.append("-lineinfo")
        elif task.deviceDebugLevel == 2:
            options.append("-G")

    def translate_device_extras(self, options, task):
        if self.relocatableDeviceCode:
            options.append("-rdc=true")
        else:
            options.append("-rdc=false")

    def translate_pch(self, options, task):
        if task.usePCH:
            headerPathEsc = binutils_esc_path(task.usePCH)
            options.append("-include \"%s\"" % headerPathEsc)

    def translate_linker_inputs(self, options, task):
        for input in task.inputs:
            libName = get_lib_name(input)
            if libName:
                libDir = os.path.dirname(input)
                libDirEsc = binutils_esc_path(libDir)
                options.append("-L\"%s\"" % libDirEsc)
                options.append("-l\"%s\"" % libName)
            else:
                inputEsc = binutils_esc_path(input)
                options.append("\"%s\"" % inputEsc)

    def translate_cpp_options(self, options, task):
        # translate simple options first for ease of viewing
        GccToolChain.translate_opt_level(self, options, task)
        self.translate_debug_level(options, task)
        self.translate_device_debug_level(options, task)
        self.translate_warn_level(options, task)
        self.translate_address_model(options, task)
        self.translate_pch(options, task)
        GccToolChain.translate_include_paths(self, options, task)
        GccToolChain.translate_defines(self, options, task)
        options.extend(task.extraOptions)


    def emit_cpp_compile(self, project, task):
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = pynja.build.ninja_esc_path(task.outputPath)
        sourcePath = pynja.build.ninja_esc_path(task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = pynja.build.ninja_esc_path(self._cxx_script)

        # write build command
        ninjaFile.write("build %(outputPath)s  %(logPath)s : %(name)s_cxx  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s" % locals())
        pynja.build.translate_extra_deps(ninjaFile, task, False)
        ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
        pynja.build.translate_order_only_deps(ninjaFile, task, False)
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
        self.translate_cpp_options(options, task)
        write_rsp_file(project, task, options)

    def emit_static_lib(self, project, task):
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = pynja.build.ninja_esc_path(task.outputPath)
        logPath = outputPath + ".log"
        outputName = os.path.basename(task.outputPath)
        scriptPath = pynja.build.ninja_esc_path(self._invoke_script)

        ninjaFile.write("build %(outputPath)s %(logPath)s : %(name)s_invoke | %(outputPath)s.rsp %(scriptPath)s" % locals())
        pynja.build.translate_path_list(ninjaFile, task.inputs)
        pynja.build.translate_extra_deps(ninjaFile, task, False)
        ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
        pynja.build.translate_order_only_deps(ninjaFile, task, False)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")

        # write response file
        options = []
        options.append("-lib")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("-o \"%s\"" % outputFileEsc)
        self.translate_linker_inputs(options, task)
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
        scriptPath = pynja.build.ninja_esc_path(self._invoke_script)

        ninjaFile.write("build %(outputPath)s %(libraryPath)s %(logPath)s : %(name)s_invoke | %(outputPath)s.rsp %(scriptPath)s" % locals())
        for input in task.inputs:
            if os.path.isabs(input):
                inputEsc = pynja.build.ninja_esc_path(input)
                ninjaFile.write(" ")
                ninjaFile.write(inputEsc)
        pynja.build.translate_extra_deps(ninjaFile, task, False)
        ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
        pynja.build.translate_order_only_deps(ninjaFile, task, False)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")

        # write response file
        options = []
        options.append("-link")
        if not task.makeExecutable:
            options.append("-shared")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("-o \"%s\"" % outputFileEsc)
        self.translate_address_model(options, task)
        if task.keepDebugInfo and "msvc" in self.hostCompiler:
            options.append("-Xlinker /DEBUG")
        elif not task.keepDebugInfo and "gcc" in self.hostCompiler:
            options.append("-Xlinker --strip-debug")
        self.translate_linker_inputs(options, task)
        options.extend(task.extraOptions)
        write_rsp_file(project, task, options)


if os.name == "nt":
    class MsvcToolChain(pynja.build.ToolChain):
        """A toolchain object capable of driving msvc 8.0 and greater."""

        def __init__(self, name, installDir, arch):
            super().__init__(name)
            self.installDir = installDir
            self.arch = arch
            self.objectFileExt = ".obj"
            self.pchFileExt = ".pch"
            # MSVC does support PCHs, but due to error 2858 it's disabled here for now.
            # The error is that the PCH must use the same PDB as the compilation units;
            # this prevents arbitrary re-use of PCH files.
            self.supportsPCH = True
            self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
            self._cxx_script  = os.path.join(self._scriptDir, "msvc-cxx-invoke.py")
            self._lib_script  = os.path.join(self._scriptDir, "msvc-lib-invoke.py")
            self._link_script = os.path.join(self._scriptDir, "msvc-link-invoke.py")

        def emit_rules(self, ninjaFile):
            ninjaFile.write("#############################################\n")
            ninjaFile.write("# %s\n" % self.name)
            ninjaFile.write("\n")
            ninjaFile.write("rule %s_cxx\n" % self.name)
            ninjaFile.write("  depfile = $DEP_FILE\n")
            ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OBJ_FILE\"  \"$PDB_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._cxx_script, self.installDir, self.arch))
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
            elif 1 <= task.optLevel <= 2:
                options.append("/O" + str(task.optLevel))
            elif task.optLevel == 3:
                options.append("/Ox")
            else:
                raise Exception("invalid optimization level: " + str(task.optLevel))

        def translate_debug_level(self, options, task):
            if not (0 <= task.debugLevel <= 3):
                raise Exception("invalid debug level: " + str(task.debugLevel))

            if task.debugLevel == 0:
                return

            if self.supportsPCH and (task.createPCH or task.usePCH):
                if task.debugLevel == 1:
                    options.append("/Zd")
                else:
                    options.append("/Z7")
            else:
                if task.debugLevel == 1:
                    options.append("/Zd")
                elif task.debugLevel == 2:
                    options.append("/Zi")
                elif task.debugLevel == 3:
                    options.append("/ZI")

        def translate_warn_level(self, options, task):
            if not (0 <= task.warnLevel <= 4):
                raise Exception("invalid warn level: " + str(task.warnLevel))

            # enable one-line diagnostics
            options.append("/WL")
            options.append("/W" + str(task.warnLevel))
            if task.warningsAsErrors:
                options.append("/WX")

        def translate_include_paths(self, options, task):
            for includePath in task.includePaths:
                if not includePath:
                    raise Exception("empty includePath set for: " + task.outputPath)
                options.append("/I\"%s\"" % includePath)

        def translate_defines(self, options, task):
            for define in task.defines:
                if not define:
                    raise Exception("empty define set for: " + task.outputPath)
                options.append("/D%s" % define)

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

        # note: this should be called *before* adding additional force includes
        def translate_pch(self, options, task):
            if task.createPCH:
                options.append("/TP")
                options.append("/Yc")
                if task.debugLevel > 0:
                    options.append("/Yd")
            if task.usePCH:
                if not task.usePCH.endswith(".pch"):
                    options.append("/FI\"%s\"" % task.usePCH)
                else:
                    headerPath = task.usePCH[:-4]
                    options.append("/Yu\"%s\"" % headerPath)
                    options.append("/FI\"%s\"" % headerPath)
                    options.append("/Fp\"%s\"" % task.usePCH)

        def translate_cpp_options(self, options, task):
            # translate simple options first for ease of viewing
            self.translate_opt_level(options, task)
            self.translate_debug_level(options, task)
            self.translate_warn_level(options, task)
            self.translate_crt(options, task)
            self.translate_include_paths(options, task)
            self.translate_defines(options, task)
            self.translate_pch(options, task)
            options.extend(task.extraOptions)


        def emit_cpp_compile(self, project, task):
            ninjaFile = project.projectMan.ninjaFile
            name = self.name
            outputPath = pynja.build.ninja_esc_path(task.outputPath)
            sourcePath = pynja.build.ninja_esc_path(task.sourcePath)
            logPath = outputPath + ".log"
            sourceName = os.path.basename(task.sourcePath)
            outputName = os.path.basename(task.outputPath)
            scriptPath = pynja.build.ninja_esc_path(self._cxx_script)

            outputPaths = outputPath
            if task.createPCH:
                outputPaths = "%s %s.obj" % (outputPath, outputPath)

            pdbPath = ""
            if task.debugLevel >= 1:
                if self.supportsPCH and (task.createPCH or task.usePCH):
                    # we're embedding symbols in object files, so no PDB is actually created
                    pdbPath = "none"
                else:
                    pdbPath = outputPath + ".pdb"
                    outputPaths = "%s %s" % (outputPaths, pdbPath)

            pchPath = ""
            if task.usePCH:
                pchPath = pynja.build.ninja_esc_path(task.usePCH)

            # write build command
            ninjaFile.write("build %(outputPaths)s %(logPath)s : %(name)s_cxx  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s %(pchPath)s" % locals())
            pynja.build.translate_extra_deps(ninjaFile, task, False)
            ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
            pynja.build.translate_order_only_deps(ninjaFile, task, False)
            ninjaFile.write("\n")

            ninjaFile.write("  WORKING_DIR = %s\n" % task.workingDir)
            ninjaFile.write("  SRC_FILE    = %s\n" % task.sourcePath)
            ninjaFile.write("  OBJ_FILE    = %s\n" % task.outputPath)
            ninjaFile.write("  PDB_FILE    = %s\n" % pdbPath)
            ninjaFile.write("  DEP_FILE    = %s.d\n" % task.outputPath)
            ninjaFile.write("  LOG_FILE    = %s.log\n" % task.outputPath)
            ninjaFile.write("  RSP_FILE    = %s.rsp\n" % task.outputPath)
            ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
            ninjaFile.write("\n")

            # write response file
            options = []
            options.append("/nologo")
            options.append("/c")
            self.translate_cpp_options(options, task)
            write_rsp_file(project, task, options)

            if task.createPCH:
                project.projectMan.emit_copy(task.sourcePath, task.outputPath[:-4])

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
            ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
            pynja.build.translate_order_only_deps(ninjaFile, task, False)
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
            ninjaFile.write(" || %s" % project.projectMan.ninjaPathEsc)
            pynja.build.translate_order_only_deps(ninjaFile, task, False)
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
