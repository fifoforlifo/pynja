import os
import sys
import re
import nvcc_common


script, workingDir, logPath, installDir, hostCompiler, hostInstallDir, addressModel, rspPath = sys.argv

rspPathEsc = nvcc_common.escape_path(rspPath)


def invoke():
    if "msvc" in hostCompiler:
        forceCompilerOption = nvcc_common.calc_msvc_options(hostCompiler)
    else:
        forceCompilerOption = ""
    cmd = "nvcc %s -optf \"%s\" > \"%s\" 2>&1" % (forceCompilerOption, rspPathEsc, logPath)
    exitcode = os.system(cmd)
    with open(logPath, "rt") as logFile:
        logContents = logFile.read()
    if re.search("(warning)|(error)", logContents, re.MULTILINE):
        print("%s" % logContents)
    if exitcode:
        sys.exit(exitcode)


if __name__ == '__main__':
    os.chdir(workingDir)

    nvcc_common.set_nvcc_environment(installDir, hostCompiler, hostInstallDir, addressModel)

    invoke()
    sys.exit(0)
