import os
import sys
import re
import msvc_common


if __name__ == '__main__':
    script, workingDir, logPath, installDir, arch, rspPath = sys.argv


    def is_os_64bit():
        arch1 = (os.environ.get('PROCESSOR_ARCHITECTURE') or "").lower()
        arch2 = (os.environ.get('PROCESSOR_ARCHITEW6432') or "").lower()
        return (arch1 == "amd64" or arch2 == "amd64")


    def shell_escape_path(path):
        return path.replace(" ", "\\ ")


    def create_lib():
        cmd = "lib \"@%s\" > \"%s\" 2>&1 " % (rspPath, logPath)
        exitcode = os.system(cmd)
        with open(logPath, "rt") as logFile:
            logContents = logFile.read()
        if re.search("(warning)|(error)", logContents, re.MULTILINE):
            print("%s" % logContents)
        if exitcode:
            sys.exit(exitcode)


    if os.name != 'nt':
        raise Exception("msvc is only usable on Windows")
    if not (arch == "x86" or arch == "amd64"):
        raise Exception("invalid architecture: " + arch)

    os.chdir(workingDir)

    msvc_common.set_msvc_environment(installDir, arch)

    create_lib()

    sys.exit(0)
