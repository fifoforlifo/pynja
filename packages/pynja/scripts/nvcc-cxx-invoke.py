import os
import sys
import re
import nvcc_common


if __name__ == '__main__':
    script, workingDir, srcPath, objPath, depPath, logPath, installDir, hostCompiler, hostInstallDir, addressModel, rspPath = sys.argv

    srcPathEsc = nvcc_common.escape_path(srcPath)
    rspPathEsc = nvcc_common.escape_path(rspPath)
    objPathEsc = nvcc_common.escape_path(objPath)
    depPathEsc = nvcc_common.escape_path(depPath)


    def generate_deps():
        if "msvc" in hostCompiler:
            forceCompilerOption = nvcc_common.calc_msvc_options(hostCompiler)
        else:
            forceCompilerOption = ""
        tempDepPath = depPathEsc + ".tmp"
        cmd = "nvcc -M %s \"%s\" -optf \"%s\" -o \"%s\" > \"%s\" 2>&1" % (forceCompilerOption, srcPathEsc, rspPathEsc, tempDepPath, logPath)
        exitcode = os.system(cmd)

        if os.path.exists(depPath + ".tmp"):
            with open(tempDepPath, "rt") as tempDepFile:
                depLines = tempDepFile.readlines()
            os.unlink(tempDepPath)
            rhsIndex = depLines[0].find(' : ')
            depLines[0] = objPath + " : " + depLines[0][rhsIndex:]
            with open(depPath, "wt") as depFile:
                depFile.writelines(depLines)

        with open(logPath, "rt") as logFile:
            logContents = logFile.read()
        if re.search("(warning)|(error)", logContents, re.MULTILINE):
            print("%s" % logContents)
        if exitcode:
            sys.exit(exitcode)


    def cpp_compile():
        if "msvc" in hostCompiler:
            forceCompilerOption = nvcc_common.calc_msvc_options(hostCompiler)
        else:
            forceCompilerOption = ""
        cmd = "nvcc -c %s \"%s\" -optf \"%s\" -o \"%s\" > \"%s\" 2>&1" % (forceCompilerOption, srcPathEsc, rspPathEsc, objPathEsc, logPath)
        exitcode = os.system(cmd)
        with open(logPath, "rt") as logFile:
            logContents = logFile.read()
        if re.search("(warning)|(error)", logContents, re.MULTILINE):
            print("%s" % logContents)
        if exitcode:
            sys.exit(exitcode)


    os.chdir(workingDir)

    nvcc_common.set_nvcc_environment(installDir, hostCompiler, hostInstallDir, addressModel)

    generate_deps()
    cpp_compile()
    sys.exit(0)
