import os
import sys
import re


script, workingDir, logPath, installDir, prefix, suffix, rspPath = sys.argv


prefix = "" if prefix == "_NO_PREFIX_" else prefix
suffix = "" if suffix == "_NO_SUFFIX_" else prefix


def create_lib():
    cmd = "%sar%s \"@%s\" > \"%s\" 2>&1" % (prefix, suffix, rspPath, logPath)
    exitcode = os.system(cmd)
    if exitcode:
        with open(logPath, "rt") as logFile:
            contents = logFile.read()
            print(contents)
        sys.exit(exitcode)


if __name__ == '__main__':
    os.chdir(workingDir)

    oldPathEnv = os.environ.get('PATH') or ""
    os.environ['PATH'] = "%s/bin%s%s" % (installDir, os.pathsep, oldPathEnv)

    create_lib()
    sys.exit(0)
