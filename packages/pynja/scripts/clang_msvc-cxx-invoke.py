import os
import sys
import re
import msvc_common


if __name__ == '__main__':
    script, workingDir, srcPath, outputPath, pdbPath, depPath, logPath, installDir, arch, rspPath, msvcVer, llvmDir = sys.argv


    def shell_escape_path(path):
        return path.replace(" ", "\\ ")

    def set_clang_msvc_environment():
        oldPathEnv = os.environ.get('PATH') or ""
        os.environ['PATH'] = "%s\\bin;%s" % (llvmDir, oldPathEnv)
        os.environ["INCLUDE"] = "%s\\VC\\include" % installDir

    def cpp_compile():
        createPCH = outputPath.endswith(".pch")
        if createPCH:
            objectPath = outputPath + ".obj"
            extraOptions = "/Fp\"%s\"" % outputPath
        else:
            objectPath = outputPath
            extraOptions = ""

        if arch == "x86":
            extraOptions += " -m32"
        else:
            extraOptions += " -m64"

        mscVerMap = {
             "8" : "1400",
             "9" : "1500",
            "10" : "1600",
            "11" : "1700",
            "12" : "1800",
            "14" : "1900",
        }
        extraOptions += " -fmsc-version=" + mscVerMap[msvcVer]

        cmd = "clang-cl /showIncludes \"%s\" \"@%s\" \"/Fo%s\" -D_HAS_EXCEPTIONS=0 %s > \"%s\" 2>&1" % (srcPath, rspPath, objectPath, extraOptions, logPath)
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

    set_clang_msvc_environment()

    cpp_compile()

    sys.exit(0)
