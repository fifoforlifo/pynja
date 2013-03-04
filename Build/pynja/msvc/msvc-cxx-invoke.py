import os
import sys
import re


script, workingDir, srcPath, objPath, depPath, logPath, installDir, arch, rspPath = sys.argv


def is_os_64bit():
    arch1 = (os.environ.get('PROCESSOR_ARCHITECTURE') or "").lower()
    arch2 = (os.environ.get('PROCESSOR_ARCHITEW6432') or "").lower()
    return (arch1 == "amd64" or arch2 == "amd64")


def shell_escape_path(path):
    return path.replace(" ", "\\ ")


def generate_deps():
    ppPath = objPath + ".pp"
    siPath = objPath + ".si"
    cmd = "cl /showIncludes /E \"%s\" \"@%s\" 1>\"%s\" 2>\"%s\" " % (srcPath, rspPath, ppPath, siPath)
    exitcode = os.system(cmd)
    if exitcode:
        with open(siPath, "rt") as logFile:
            contents = logFile.read()
            print(contents)
        os.unlink(siPath)
        os.unlink(ppPath)
        sys.exit(exitcode)

    with open(siPath, "rt") as siFile:
        siLines = siFile.readlines()
    with open(depPath, "wt") as depFile:
        objPathEsc = shell_escape_path(objPath)
        depFile.write("%s: \\\n" % objPathEsc)
        for siLine in siLines:
            match = re.match("Note: including file: ([ ]*)(.*)", siLine)
            if match:
                depEsc = shell_escape_path(match.group(2))
                depFile.write("%s \\\n" % depEsc)
    os.unlink(siPath)
    os.unlink(ppPath)


def cpp_compile():
    cmd = "cl \"%s\" \"@%s\" \"/Fo%s\" > \"%s\" 2>&1 " % (srcPath, rspPath, objPath, logPath)
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

    generate_deps()
    cpp_compile()

    sys.exit(0)
