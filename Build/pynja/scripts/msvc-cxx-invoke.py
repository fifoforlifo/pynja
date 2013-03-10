import os
import sys
import re
import msvc_common


script, workingDir, srcPath, outputPath, pdbPath, depPath, logPath, installDir, arch, rspPath = sys.argv


def is_os_64bit():
    arch1 = (os.environ.get('PROCESSOR_ARCHITECTURE') or "").lower()
    arch2 = (os.environ.get('PROCESSOR_ARCHITEW6432') or "").lower()
    return (arch1 == "amd64" or arch2 == "amd64")


def shell_escape_path(path):
    return path.replace(" ", "\\ ")


def generate_deps(outputPath, srcPath, rspPath, depPath):
    ppPath = outputPath + ".pp"
    siPath = outputPath + ".si"
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
        outputPathEsc = shell_escape_path(outputPath)
        depFile.write("%s: \\\n" % outputPathEsc)
        for siLine in siLines:
            match = re.match("Note: including file: ([ ]*)(.*)", siLine)
            if match:
                depEsc = shell_escape_path(match.group(2))
                depFile.write("%s \\\n" % depEsc)
    os.unlink(siPath)
    os.unlink(ppPath)


def cpp_compile():
    createPCH = outputPath.endswith(".pch")
    if createPCH:
        objectPath = outputPath + ".obj"
        extraOptions = "/Fp\"%s\"" % outputPath
    else:
        objectPath = outputPath
        extraOptions = ""

    cmd = "cl \"%s\" \"@%s\" \"/Fo%s\" \"/Fd%s\" %s > \"%s\" 2>&1 " % (srcPath, rspPath, objectPath, pdbPath, extraOptions, logPath)
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

    generate_deps(outputPath, srcPath, rspPath, depPath)
    cpp_compile()

    sys.exit(0)
