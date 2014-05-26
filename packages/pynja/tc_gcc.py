import os
from .tc import *
from . import build


def binutils_esc_path(path):
    return path.replace("\\", "/")

def get_lib_name(path):
    if path.endswith(".a"):
        fname = os.path.basename(path)
        if fname.startswith("lib"):
            return fname[3:-2]
    return None


class GccToolChain(build.ToolChain):
    """A toolchain object capable of driving gcc commandlines."""

    def __init__(self, name, installDir, prefix = "", suffix = ""):
        super().__init__(name)
        self.installDir = installDir
        self.prefix = prefix
        self.suffix = suffix
        self.objectFileExt = ".o"
        self.pchFileExt = ".gch"
        self.supportsPCH = True
        self._scriptDir = os.path.join(os.path.dirname(__file__), "scripts")
        self._cxx_script  = os.path.join(self._scriptDir, "gcc-cxx-invoke.py")
        self._lib_script  = os.path.join(self._scriptDir, "gcc-lib-invoke.py")
        self._link_script = os.path.join(self._scriptDir, "gcc-link-invoke.py")
        # Conservatively set LTO support to False.
        self.ltoSupport = False

    def emit_rules(self, ninjaFile):
        arName = "%sar%s" % (self.prefix, self.suffix)

        ninjaFile.write("#############################################\n")
        ninjaFile.write("# %s\n" % self.name)
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_cxx\n" % self.name)
        ninjaFile.write("  depfile = $DEP_FILE\n")
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$SRC_FILE\"  \"$OBJ_FILE\"  \"$DEP_FILE\"  \"$LOG_FILE\"  \"%s\"  $TOOL_NAME  \"$RSP_FILE\"\n" % (self._cxx_script, self.installDir))
        ninjaFile.write("  description = %s_cxx  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_lib\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  %s  \"$RSP_FILE\"\n" % (self._lib_script, self.installDir, arName))
        ninjaFile.write("  description = %s_lib  $DESC\n" % self.name)
        ninjaFile.write("  restat = 1\n")
        ninjaFile.write("\n")
        ninjaFile.write("rule %s_link\n" % self.name)
        ninjaFile.write("  command = python \"%s\"  \"$WORKING_DIR\"  \"$LOG_FILE\"  \"%s\"  $TOOL_NAME  \"$RSP_FILE\"\n" % (self._link_script, self.installDir))
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
        if task.optLevel >= 2:
            if task.lto:
                options.append("-flto")

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
    def is_c_dialect(self, std):
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
            return True
        else:
            return False

    def get_language_option(self, std):
        if self.is_c_dialect(std):
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
                task.extraDeps.append(task.usePCH[:-4])
                task.extraDeps.append(task.usePCH)
            else:
                headerPathEsc = binutils_esc_path(task.usePCH)
                task.extraDeps.append(task.usePCH)
            options.append("-include \"%s\"" % headerPathEsc)
            options.append("-H")
            options.append("-Winvalid-pch")

    def translate_dialect(self, options, task):
        if task.std:
            options.append("-std=%s" % task.std)


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
        # write response file
        options = []
        options.append("-c")
        self.translate_cpp_options(options, task)
        write_rsp_file(project, task, options)

        if task.createPCH:
            # Create a copy of the source header, which will reside next to the
            # PCH file, and will be force-included.
            project.projectMan.emit_copy(task.sourcePath, task.outputPath[:-4])

        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = build.xlat_path(project, task.outputPath)
        sourcePath = build.xlat_path(project, task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._cxx_script)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

        # write build command
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(name)s_cxx  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s" % locals())
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
        ninjaFile.write("  SRC_FILE    = %s\n" % sourcePath)
        ninjaFile.write("  OBJ_FILE    = %s\n" % outputPath)
        ninjaFile.write("  DEP_FILE    = %s.d\n" % outputPath)
        ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % outputPath)
        ninjaFile.write("  TOOL_NAME   = %s%s%s\n" % (self.prefix, "g++", self.suffix))
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")

    def emit_static_lib(self, project, task):
        # write response file
        options = []
        options.append("rc")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("\"%s\"" % outputFileEsc)
        self.translate_linker_inputs(options, task)
        write_rsp_file(project, task, options)

        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = build.xlat_path(project, task.outputPath)
        logPath = outputPath + ".log"
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._lib_script)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(name)s_lib | %(outputPath)s.rsp %(scriptPath)s" % locals())
        build.translate_path_list(ninjaFile, project, task.inputs)
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
        ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % outputPath)
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")

    def emit_link(self, project, task):
        # write response file
        options = []
        if not task.makeExecutable:
            options.append("-shared")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("-o \"%s\"" % outputFileEsc)
        self.translate_address_model(options, task)
        if not task.keepDebugInfo:
            options.append("--strip-debug")
        if task.lto:
            options.append("-O3")
            options.append("-flto")
        if task.noUndefined:
            options.append("-Wl,--no-undefined")
        self.translate_linker_inputs(options, task)
        options.extend(task.extraOptions)
        write_rsp_file(project, task, options)

        # emit ninja file contents
        ninjaFile = project.projectMan.ninjaFile
        name = self.name
        outputPath = build.xlat_path(project, task.outputPath)
        libraryPath = ""
        if task.outputLibraryPath and (task.outputLibraryPath != task.outputPath):
            libraryPath = build.xlat_path(project, task.outputLibraryPath)
        logPath = outputPath + ".log"
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._lib_script)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(libraryPath)s %(logPath)s : %(name)s_link | %(outputPath)s.rsp %(scriptPath)s" % locals())
        for input in task.inputs:
            if os.path.isabs(input):
                inputEsc = build.ninja_esc_path(input)
                ninjaFile.write(" ")
                ninjaFile.write(inputEsc)
        build.translate_extra_deps(ninjaFile, project, task, False)
        build.translate_order_only_deps(ninjaFile, project, task, True)
        ninjaFile.write("\n")

        ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
        ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
        ninjaFile.write("  RSP_FILE    = %s.rsp\n" % outputPath)
        ninjaFile.write("  TOOL_NAME   = %s%s%s\n" % (self.prefix, "g++", self.suffix))
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")
