import os
import sys
import re
import gcc_common


script, workingDir, logPath, installDir, toolName, rspPath = sys.argv


def link():
    cmd = "%s \"@%s\" > \"%s\" 2>&1" % (toolName, rspPath, logPath)
    exitcode = os.system(cmd)
    with open(logPath, "rt") as logFile:
        logContents = logFile.read()
    if re.search("(warning)|(error)", logContents, re.MULTILINE):
        print("%s" % logContents)
    if exitcode:
        sys.exit(exitcode)


if __name__ == '__main__':
    os.chdir(workingDir)

    gcc_common.set_gcc_environment(installDir)

    link()
    sys.exit(0)
