import os
import sys


if __name__ == '__main__':
    script, protocPath, workingDir, sourcePath, outputPath, depPath, logPath, rspPath = sys.argv


    def shell_escape_path(path):
        return path.replace(" ", "\\ ")


    def extract_include_paths(optionsStr):
        endindex = optionsStr.find("|||")
        sanitizedOptionsStr = (optionsStr[0:endindex]).replace("\n", " ")
        rawOptions = sanitizedOptionsStr.split()
        includePaths = [str[3:-1] for str in rawOptions]
        return includePaths


    def calc_abs_import_path(includePaths, importedPath):
        if os.path.isabs(importedPath):
            return importedPath
        for includePath in includePaths:
            absPath = os.path.join(includePath, importedPath)
            if os.path.exists(absPath):
                return absPath


    def calc_deps(includePaths, filePaths, sourceContents):
        for sourceLine in sourceContents.splitlines():
            line = sourceLine.strip()
            if line.startswith("import"):
                line = line[6:].strip()
                if line.startswith("public"):
                    line = line[6:].strip()
                assert(line[0] == '"')
                endindex = line.find('"', 1)
                importedPath = line[1:endindex]
                absPath = calc_abs_import_path(includePaths, importedPath)
                if absPath not in filePaths:
                    filePaths.add(absPath)
                    with open(absPath, "rt") as importedFile:
                        importedContents = importedFile.read()
                        calc_deps(includePaths, filePaths, importedContents)


    def generate_deps(includePaths):
        filePaths = set()
        filePaths.add(sourcePath)
        with open(sourcePath, "rt") as sourceFile:
            sourceContents = sourceFile.read()
            calc_deps(includePaths, filePaths, sourceContents)

        with open(depPath, "wt") as depFile:
            outputPathEsc = shell_escape_path(outputPath)
            depFile.write("%s: \\\n" % outputPathEsc)
            for filePath in filePaths:
                depEsc = shell_escape_path(filePath)
                depFile.write("%s \\\n" % depEsc)


    def invoke(optionsStr):
        sanitizedOptionsStr = optionsStr.replace("|||", " ").replace("\n", " ")
        cmd = "%s %s \"%s\" > \"%s\" 2>&1" % (protocPath, sanitizedOptionsStr, sourcePath, logPath)
        exitcode = os.system(cmd)
        if exitcode:
            with open(logPath, "rt") as logFile:
                logContents = logFile.read()
                print(logContents)
            sys.exit(exitcode)


    os.chdir(workingDir)

    with open(rspPath, "rt") as rspFile:
        optionsStr = rspFile.read()

    includePaths = extract_include_paths(optionsStr)

    invoke(optionsStr)
    # Generate deps only if the actual proto compiler accepted the input;
    # this lets us assume a well-formed input.
    generate_deps(includePaths)
    sys.exit(0)
