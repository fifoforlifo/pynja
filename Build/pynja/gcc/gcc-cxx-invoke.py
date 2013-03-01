import os
import sys
import re


script, workingDir, srcPath, objPath, depPath, logPath, installDir, prefix, suffix, rspPath = sys.argv


prefix = "" if prefix == "_NO_PREFIX_" else prefix
suffix = "" if suffix == "_NO_SUFFIX_" else prefix


def cpp_compile():
    cmd = "%sgcc%s \"%s\" \"@%s\" -o\"%s\" -MD -MF \"%s\" > \"%s\" 2>&1" % (prefix, suffix, srcPath, rspPath, objPath, depPath, logPath)
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
    os.environ['INCLUDE'] = "%s/include" % installDir
    os.environ['LIB'] = "%s/lib" % installDir

    cpp_compile()
    sys.exit(0)
