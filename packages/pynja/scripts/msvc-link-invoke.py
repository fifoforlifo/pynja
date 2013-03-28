import os
import sys
import re
import msvc_common


script, workingDir, logPath, installDir, arch, rspPath = sys.argv


def shell_escape_path(path):
    return path.replace(" ", "\\ ")


def link():
    cmd = "link \"@%s\" > \"%s\" 2>&1 " % (rspPath, logPath)
    exitcode = os.system(cmd)
    with open(logPath, "rt") as logFile:
        logContents = logFile.read()
    if re.search("(warning)|(error)", logContents, re.MULTILINE):
        print("%s" % logContents)
    if exitcode:
        sys.exit(exitcode)


if __name__ == '__main__':
    if os.name != 'nt':
        raise Exception("msvc is only usable on Windows")
    if not (arch == "x86" or arch == "amd64"):
        raise Exception("invalid architecture: " + arch)

    os.chdir(workingDir)

    msvc_common.set_msvc_environment(installDir, arch)

    link()

    sys.exit(0)
