import os
import pynja
import repo

@pynja.project
class boost_build(repo.CppProject):
    def emit(self):
        if 'msvc' in self.variant.toolchain:
            projectDir = self.projectDir
            boostDir = pynja.rootPaths.boost150
            vcVer = self.variant.toolchain[4:]
            vcDir = getattr(pynja.rootPaths, 'msvc' + vcVer)
            arch = self.variant.arch
            if self.variant.crt == 'dcrt':
                runtimeLink = 'shared'
            else:
                runtimeLink = 'static'
            if self.variant.config == 'dbg':
                config = 'debug'
            else:
                config = 'release'

            stageDir = os.path.join(pynja.rootPaths.boost150, "stage", arch)
            self.stageDir = stageDir

            guardFileBase = "%(stageDir)s\\msvc%(vcVer)s-%(config)s-%(arch)s-%(runtimeLink)s" % locals()
            # If you want to trigger a new boost build, increment this number and submit a change.
            # The build server will pick up the changed script file, ninja will notice it's dirty,
            # this script will see the new guardFilePath doesn't exist, and boost build (b2) will be executed.
            guardCounter = 0x00000000
            guardFilePath = "%(guardFileBase)s_%(guardCounter)08x.txt" % locals()
            logFilePath = "%(guardFileBase)s.log" % locals()

            script = "%s\\boost-b2-msvc-invoke.py" % self.projectDir
            cmd = r'python %(script)s  "%(boostDir)s" %(vcVer)s "%(vcDir)s" %(arch)s %(runtimeLink)s %(config)s "%(stageDir)s" "%(logFilePath)s" "%(guardFileBase)s" "%(guardFilePath)s"' % locals()
            outputs = [guardFilePath, logFilePath]


            libnames = [
                "chrono",
                "date_time",
                #"exception",
                "filesystem",
                #"graph",
                #"graph_parallel",
                #"iostreams",
                "locale",
                #"math", --> expands out to the following variants
                "math_c99f", "math_c99l", "math_c99",
                "math_tr1f", "math_tr1l", "math_tr1",
                #"mpi",
                "program_options",
                #"python",
                "regex",
                #"serialization",
                #"signals",
                "system",
                #"test",
                "thread",
                "timer",
                #"wave",
            ]
            for libname in libnames:
                self._add_outputs(outputs, libname)

            self.projectMan.emit_custom_command(cmd, "boost_build", [script], outputs)

        else:
            # assume boost already built
            pass

    def calc_lib_basepath(self, name, linkShared):
        variant = self.variant
        boostVer = "1_50"
        if 'msvc' in variant.toolchain:
            vcVer = variant.toolchain[4:]
            boostBuild = self.get_project("boost_build", self.variant)
            debug = ""
            if variant.config == 'dbg':
                if variant.crt == 'dcrt':
                    debug = "-gd"
                else:
                    debug = "-sgd"

            if linkShared:
                basename = "boost_%s-vc%s0-mt%s-%s" % (name, vcVer, debug, boostVer)
                basepath = os.path.join(self.stageDir, "lib", basename)
                return basepath
            else:
                basename = "libboost_%s-vc%s0-mt%s-%s" % (name, vcVer, debug, boostVer)
                basepath = os.path.join(self.stageDir, "lib", basename)
                return basepath
        else:
            raise Exception("TODO: gcc boost dependencies")

    def _add_outputs(self, outputs, name):
        variant = self.variant
        basepathShared = self.calc_lib_basepath(name, True)
        basepathStatic = self.calc_lib_basepath(name, False)
        if 'msvc' in variant.toolchain:
            outputs.append(basepathShared + ".lib")
            outputs.append(basepathShared + ".dll")
            outputs.append(basepathStatic + ".lib")
        else:
            raise Exception("TODO: gcc boost dependencies")
