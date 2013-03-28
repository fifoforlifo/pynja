import os
import sys
import re
import gcc_common


script, workingDir, logPath, installDir, prefix, suffix, rspPath = sys.argv


prefix = "" if prefix == "_NO_PREFIX_" else prefix
suffix = "" if suffix == "_NO_SUFFIX_" else prefix


def create_lib():
    cmd = "%sar%s \"@%s\" > \"%s\" 2>&1" % (prefix, suffix, rspPath, logPath)
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

    create_lib()
    sys.exit(0)
