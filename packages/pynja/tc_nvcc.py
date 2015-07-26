import os
from . import build
from .tc_cpp import *
from .tc_gcc import *
from .tc_msvc import *


class NvccToolChain(CppToolChain):
    """A toolchain object capable of driving nvcc (CUDA compiler)."""

    # hostCompiler = {gcc, msvc}
    def __init__(self, name, installDir, hostCompiler, hostInstallDir, addressModel, targetWindows):
        super().__init__(name, targetWindows)
        self.installDir = installDir
        self.hostCompiler = hostCompiler
        self.hostInstallDir = hostInstallDir
        self.addressModel = addressModel
        if "msvc" in self.hostCompiler:
            self.objectFileExt = ".obj"
            self.pchFileExt = ".pch"
            self.ltoSupport = True
            self.arch = "x86" if addressModel == "-m32" else "amd64"
            # The Windows SDK / Windows Kit version and path.
            self.winsdkVer = None
            self.winsdkDir = None
            # If True, default include-paths and libraries will be assigned.
            self.winsdkDefaults = True
        else:
            self.objectFileExt = ".o"
            self.pchFileExt = ".gch"
            self.ltoSupport = False
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
            task.extraDeps.append(task.usePCH)

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
        if "msvc" in self.hostCompiler:
            if self.winsdkDefaults:
                if self.winsdkVer < 80:
                    task.includePaths.insert(0, os.path.join(self.winsdkDir, "Include"))
                else:
                    task.includePaths.insert(0, os.path.join(self.winsdkDir, "Include", "shared"))
                    task.includePaths.insert(0, os.path.join(self.winsdkDir, "Include", "um"))
        options.extend(self.defaultCppOptions)
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
        # write response file
        options = []
        self.translate_cpp_options(options, task)
        write_rsp_file(project, task, options)

        # emit ninja file contents
        name = self.name
        outputPath = build.xlat_path(project, task.outputPath)
        sourcePath = build.xlat_path(project, task.sourcePath)
        logPath = outputPath + ".log"
        sourceName = os.path.basename(task.sourcePath)
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._cxx_script)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

        # write build command
        ninjaFile = project.projectMan.ninjaFile
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
        ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
        ninjaFile.write("\n")

    def emit_static_lib(self, project, task):
        # write response file
        options = []
        options.append("-lib")
        outputFileEsc = binutils_esc_path(task.outputPath)
        options.append("-o \"%s\"" % outputFileEsc)
        self.translate_linker_inputs(options, task)
        write_rsp_file(project, task, options)

        # emit ninja file contents
        name = self.name
        outputPath = build.xlat_path(project, task.outputPath)
        logPath = outputPath + ".log"
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._invoke_script)

        extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

        ninjaFile = project.projectMan.ninjaFile
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(name)s_invoke | %(outputPath)s.rsp %(scriptPath)s" % locals())
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
        if "msvc" in self.hostCompiler:
            if self.winsdkDefaults:
                winsdkLibDir = calc_winsdk_lib_dir(self)
                task.inputs.append(os.path.join(winsdkLibDir, "kernel32.lib"))
                task.inputs.append(os.path.join(winsdkLibDir, "user32.lib"))
                task.inputs.append(os.path.join(winsdkLibDir, "gdi32.lib"))
                task.inputs.append(os.path.join(winsdkLibDir, "uuid.lib"))

        name = self.name
        outputPath = build.xlat_path(project, task.outputPath)
        libraryPath = ""
        if task.outputLibraryPath and (task.outputLibraryPath != task.outputPath):
            libraryPath = build.xlat_path(project, task.outputLibraryPath)
        logPath = outputPath + ".log"
        outputName = os.path.basename(task.outputPath)
        scriptPath = build.ninja_esc_path(self._invoke_script)

        extraOutputs = " ".join([build.ninja_esc_path(p) for p in task.extraOutputs])

        ninjaFile = project.projectMan.ninjaFile
        ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(libraryPath)s %(logPath)s : %(name)s_invoke | %(outputPath)s.rsp %(scriptPath)s" % locals())
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
        ninjaFile.write("  DESC        = %s\n" % outputName)
        ninjaFile.write("\n")
        ninjaFile.write("\n")

        # write response file
        options = []
        options.extend(self.defaultLinkOptions)
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
