import os
import sys
import re
import msvc_common


if __name__ == '__main__':
    script, workingDir, srcPath, outputPath, pdbPath, depPath, logPath, installDir, arch, rspPath = sys.argv


    def shell_escape_path(path):
        return path.replace(" ", "\\ ")


    def cpp_compile():
        createPCH = outputPath.endswith(".pch")
        if createPCH:
            objectPath = outputPath + ".obj"
            extraOptions = "/Fp\"%s\"" % outputPath
        else:
            objectPath = outputPath
            extraOptions = ""

        cmd = "cl /showIncludes \"%s\" \"@%s\" \"/Fo%s\" \"/Fd%s\" %s > \"%s\" 2>&1" % (srcPath, rspPath, objectPath, pdbPath, extraOptions, logPath)
        exitcode = os.system(cmd)

        with open(logPath, "rt") as logFile:
            logContents = logFile.read()
        needToPrintLog = not not exitcode
        # write out deps file, and determine if an error or warning occurred
        with open(depPath, "wt") as depFile:
            outputPathEsc = shell_escape_path(outputPath)
            depFile.write("%s: \\\n" % outputPathEsc)
            for logLine in logContents.splitlines():
                if " error " in logLine:
                    needToPrintLog = True
                elif " warning " in logLine:
                    if not ("D9035" in logLine): # ignore: Command line warning D9035 : option 'Yd' has been deprecated
                        needToPrintLog = True
                else:
                    match = re.match("Note: including file: ([ ]*)(.*)", logLine)
                    if match:
                        incPath = os.path.normpath(match.group(2))
                        depEsc = shell_escape_path(incPath)
                        depFile.write("%s \\\n" % depEsc)
        if needToPrintLog:
            for logLine in logContents.splitlines():
                if "D9035" in logLine:
                    continue
                if "Note: including file: " in logLine:
                    continue
                print(logLine)
        if exitcode:
            sys.exit(exitcode)


    if os.name != 'nt':
        raise Exception("msvc is only usable on Windows")
    if not (arch == "x86" or arch == "amd64"):
        raise Exception("invalid architecture: " + arch)

    os.chdir(workingDir)

    msvc_common.set_msvc_environment(installDir, arch)

    cpp_compile()

    sys.exit(0)
