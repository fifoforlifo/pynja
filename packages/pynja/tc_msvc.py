import os
from .tc_cpp import *
from . import build


if os.name == "nt":
    class MsvcToolChain(CppToolChain):
        """A toolchain object capable of driving msvc 8.0 and greater."""

        def __init__(self, name, installDir, arch):
            super().__init__(name, targetWindows=True)
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
            # MSVC always supports LTO.  (they call it LTCG)
            self.ltoSupport = True

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
                    task.extraOutputs.append(task.outputPath + ".pdb")
                    task._creatingPDB = True
                elif task.debugLevel == 3:
                    options.append("/ZI")
                    task.extraOutputs.append(task.outputPath + ".pdb")
                    task._creatingPDB = True

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

        def translate_exception_handling(self, options, task):
            if task.asyncExceptionHandling:
                options.append("/EHa")
            else:
                options.append("/EHs")
            if task.externCNoThrow:
                options.append("/EHc")

        # note: this should be called *before* adding additional force includes
        def translate_pch(self, options, task):
            if task.createPCH:
                # TODO: figure out how to support PCH chain creation; for now we must fall back
                # to force-including the usePCH's source header
                if task.usePCH:
                    headerPath = task.usePCH
                    if task.usePCH.endswith(".pch"):
                        headerPath = task.usePCH[:-4]
                    options.append("/FI\"%s\"" % headerPath)
                    task.extraDeps.append(headerPath)
                options.append("/TP")
                options.append("/Yc")
                if task.debugLevel > 0:
                    options.append("/Yd")
                task.extraOutputs.append(task.outputPath + ".obj")
            elif task.usePCH:
                if not task.usePCH.endswith(".pch"):
                    options.append("/FI\"%s\"" % task.usePCH)
                    task.extraDeps.append(task.usePCH)
                else:
                    headerPath = task.usePCH[:-4]
                    options.append("/FI\"%s\"" % headerPath)
                    options.append("/Yu\"%s\"" % headerPath)
                    options.append("/Fp\"%s\"" % task.usePCH)
                    task.extraDeps.append(headerPath)
                    task.extraDeps.append(task.usePCH)

        def translate_cpp_options(self, options, task):
            # translate simple options first for ease of viewing
            self.translate_opt_level(options, task)
            self.translate_debug_level(options, task)
            self.translate_warn_level(options, task)
            self.translate_crt(options, task)
            self.translate_exception_handling(options, task)
            self.translate_include_paths(options, task)
            self.translate_defines(options, task)
            self.translate_pch(options, task)
            options.extend(task.extraOptions)


        def emit_cpp_compile(self, project, task):
            # write response file; this also updates extraInputs/extraOutputs
            options = []
            options.append("/nologo")
            options.append("/c")
            self.translate_cpp_options(options, task)
            write_rsp_file(project, task, options)

            # emit ninja file contents
            ninjaFile = project.projectMan.ninjaFile
            name = self.name
            outputPath = build.xlat_path(project, task.outputPath)
            pdbPath = "" if not task._creatingPDB else outputPath + ".pdb"
            sourcePath = build.xlat_path(project, task.sourcePath)
            logPath = outputPath + ".log"
            sourceName = os.path.basename(task.sourcePath)
            outputName = os.path.basename(task.outputPath)
            scriptPath = build.ninja_esc_path(self._cxx_script)

            extraOutputs = " ".join([build.xlat_path(project, path) for path in task.extraOutputs])

            # write build command
            ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(name)s_cxx  %(sourcePath)s | %(outputPath)s.rsp %(scriptPath)s " % locals())
            build.translate_extra_deps(ninjaFile, project, task, False)
            build.translate_order_only_deps(ninjaFile, project, task, True)
            ninjaFile.write("\n")

            ninjaFile.write("  WORKING_DIR = %s\n" % build.xlat_path(project, task.workingDir))
            ninjaFile.write("  SRC_FILE    = %s\n" % sourcePath)
            ninjaFile.write("  OBJ_FILE    = %s\n" % outputPath)
            ninjaFile.write("  PDB_FILE    = %s\n" % pdbPath)
            ninjaFile.write("  DEP_FILE    = %s.d\n" % outputPath)
            ninjaFile.write("  LOG_FILE    = %s.log\n" % outputPath)
            ninjaFile.write("  RSP_FILE    = %s.rsp\n" % outputPath)
            ninjaFile.write("  DESC        = %s -> %s\n" % (sourceName, outputName))
            ninjaFile.write("\n")

            if task.createPCH:
                project.projectMan.emit_copy(task.sourcePath, task.outputPath[:-4])

        def emit_static_lib(self, project, task):
            # write response file
            options = []
            options.append("/nologo")
            options.append("\"/OUT:%s\"" % task.outputPath)
            for input in task.inputs:
                options.append("\"%s\"" % input)
            write_rsp_file(project, task, options)

            # emit ninja file contents
            ninjaFile = project.projectMan.ninjaFile
            name = self.name
            outputPath = build.xlat_path(project, task.outputPath)
            logPath = outputPath + ".log"
            outputName = os.path.basename(task.outputPath)
            scriptPath = build.ninja_esc_path(self._lib_script)

            extraOutputs = " ".join([build.xlat_path(project, path) for paths in task.extraOutputs])

            ninjaFile.write("build %(outputPath)s %(extraOutputs)s %(logPath)s : %(name)s_lib | %(outputPath)s.rsp %(scriptPath)s " % locals())
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

            ninjaFile.write("build %(outputPath)s %(libraryPath)s %(extraOutputs)s %(logPath)s : %(name)s_link | %(outputPath)s.rsp %(scriptPath)s " % locals())
            for input in task.inputs:
                if os.path.isabs(input):
                    inputEsc = build.xlat_path(project, input)
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
else:
    class MsvcToolChain(build.ToolChain):
        """A stub implementation for non-Windows OSes."""

        def __init__(self, name, installDir, arch):
            raise Exception("MSVC not supported on non-Windows OSes.")
