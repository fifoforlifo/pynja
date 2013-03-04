import os
import sys


script, workingDir, logPath, installDir, arch, rspPath = sys.argv


def is_os_64bit():
    arch1 = (os.environ.get('PROCESSOR_ARCHITECTURE') or "").lower()
    arch2 = (os.environ.get('PROCESSOR_ARCHITEW6432') or "").lower()
    return (arch1 == "amd64" or arch2 == "amd64")


def shell_escape_path(path):
    return path.replace(" ", "\\ ")


def link():
    cmd = "link \"@%s\" > \"%s\" 2>&1 " % (rspPath, logPath)
    exitcode = os.system(cmd)
    if exitcode:
        with open(logPath, "rt") as logFile:
            contents = logFile.read()
            print(contents)
        sys.exit(exitcode)


if __name__ == '__main__':
    if os.name != 'nt':
        raise Exception("msvc is only usable on Windows")
    if not (arch == "x86" or arch == "amd64"):
        raise Exception("invalid architecture: " + arch)

    os.chdir(workingDir)

    oldPathEnv = os.environ.get('PATH') or ""

    os.environ["INCLUDE"] = "%s\\VC\\include" % installDir
    if arch == "x86":
        os.environ['LIB'] = "%s\\VC\\lib" % installDir
        os.environ['PATH'] = "%s\\VC\\bin;%s\\Common7\\IDE;%s" % (installDir, installDir, oldPathEnv)
    elif arch == "amd64":
        os.environ['LIB'] = "%s\\VC\\lib\\amd64" % installDir
        if is_os_64bit() and os.path.exists("%s\\VC\\bin\\amd64" % installDir):
            os.environ['PATH'] = "%s\\VC\\bin\\amd64;%s\\Common7\\IDE;%s" % (installDir, installDir, oldPathEnv)
        else:
            os.environ['PATH'] = "%s\\VC\\bin\\x86_amd64;%s\\Common7\\IDE;%s" % (installDir, installDir, oldPathEnv)
    else:
        raise Exception("Unexpected arch ... should not be reachable ...")

    link()

    sys.exit(0)
