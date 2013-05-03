import os
import glob
import sys
import re


script, subCommand, workingDir, jdkDir, outputDir, optionsPath, classPathsPath, sourcesPath, logPath, listFilePath, faninPath = sys.argv


def generate_list_file():
    with open(sourcesPath, "rt") as sourcesFile:
        sourcesList = sourcesFile.readlines()

    with open(listFilePath, "wt") as listFile:
        for sourcePath in sourcesList:
            if os.path.isabs(sourcePath):
                # TODO: handle this better
                print("error: cannot handle outputs for absolute source paths:\n    %s", sourcePath)
                exit(1)
            else:
                # strip off ".java" and normalize slashes
                basePath = os.path.normpath(os.path.join(outputDir, sourcePath)[0:-5])
                listFile.write("%s.class\n" % basePath)
                implicitOutputs = glob.glob("%s$*.class" % basePath)
                for implicitOutput in implicitOutputs:
                    listFile.write("%s\n" % implicitOutput)


def create_class_path_options_file(fileName):
    with open(classPathsPath, "rt") as classPathsFile:
        classPathList = classPathsFile.readlines()
    with open(fileName, "wt") as file:
        file.write("-classpath \".")
        for classPath in classPathList:
            file.write(os.pathsep)
            file.write(classPath.replace("\\", "/"))
        file.write("\"")
        file.write(" -implicit:none")


def java_compile():
    if os.path.exists(listFilePath):
        os.unlink(listFilePath)
    cpOptionsPath = classPathsPath + ".t"
    create_class_path_options_file(cpOptionsPath)

    cmd = "javac \"@%s\" \"@%s\" \"@%s\" -d \"%s\" > \"%s\" 2>&1" % (optionsPath, cpOptionsPath, sourcesPath, outputDir, logPath)
    exitcode = os.system(cmd)

    os.unlink(cpOptionsPath)

    with open(logPath, "rt") as logFile:
        logContents = logFile.read()
    if re.search("warning:|error:", logContents, re.MULTILINE):
        print("%s" % logContents)
    if exitcode:
        sys.exit(exitcode)

    generate_list_file()


def escape_path(path):
    return path.replace(" ", "\\ ").replace("$", "\\$")

def all_paths_exist(pathList):
    for path in pathList:
        if not os.path.exists(path):
            return False
    return True

def generate_fanin_file():
    if os.path.exists(faninPath):
        os.unlink(faninPath)
    # do not unlink the faninDeps file, so that upon error it remains dirty

    with open(listFilePath, "rt") as listFile:
        pathList = [path.rstrip() for path in listFile.readlines()]

    # if any implicit-output was deleted, redo the build command
    if not all_paths_exist(pathList):
        java_compile()

    faninDepsPath = faninPath + ".d"
    with open(faninDepsPath, "wt") as faninDepsFile:
        faninDepsFile.write("%s: \\\n" % escape_path(faninPath))
        for path in pathList:
            faninDepsFile.write("%s \\\n" % escape_path(path))

    with open(faninPath, "wt") as faninFile:
        faninFile.write("1")


if __name__ == '__main__':
    os.chdir(workingDir)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    oldPathEnv = os.environ['PATH']
    os.environ['PATH'] = "%s%sbin%s%s" % (jdkDir, os.sep, os.pathsep, oldPathEnv)
    os.environ['JAVA_HOME'] = "%s\jre" % (jdkDir)

    if subCommand == "compile":
        java_compile()
    elif subCommand == "fanin":
        generate_fanin_file()
    else:
        print("error: unknown subCommand")
        sys.exit(1)

    sys.exit(0)
