import os
import sys
import re
import gcc_common


if __name__ == '__main__':
    script, workingDir, srcPath, objPath, depPath, logPath, installDir, executable, rspPath = sys.argv

    def cpp_compile():
        cmd = "%s \"@%s\" \"%s\" -o\"%s\" -MD -MF \"%s\" > \"%s\" 2>&1" % (executable, rspPath, srcPath, objPath, depPath, logPath)
        exitcode = os.system(cmd)
        with open(logPath, "rt") as logFile:
            logContents = logFile.read()
        if re.search("(warning)|(error)", logContents, re.MULTILINE):
            print("%s" % logContents)
        if exitcode:
            sys.exit(exitcode)

    os.chdir(workingDir)

    gcc_common.set_gcc_environment(installDir)

    cpp_compile()
    sys.exit(0)
