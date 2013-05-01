import os
import glob
import sys
import re


script, workingDir, jdkDir, outputDir, optionsPath, classPathsPath, sourcesPath, logPath, listFilePath = sys.argv


def generate_list_file():
    with open(sourcesPath, "rt") as sourcesFile:
        sourcesList = sourcesFile.readlines()
    with open(classPathsPath, "rt") as classPathsFile:
        classPathsList = classPathsFile.readlines()

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

        for classPath in classPathsList:
            jarFilePaths = glob.glob("%s/*.jar" % classPath)
            for jarFilePath in jarFilePaths:
                listFile.write("%s\n" % jarFilePath)


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

    #os.unlink(cpOptionsPath)

    with open(logPath, "rt") as logFile:
        logContents = logFile.read()
    if re.search("warning:|error:", logContents, re.MULTILINE):
        print("%s" % logContents)
    if exitcode:
        sys.exit(exitcode)


if __name__ == '__main__':
    os.chdir(workingDir)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    oldPathEnv = os.environ['PATH']
    os.environ['PATH'] = "%s%sbin%s%s" % (jdkDir, os.sep, os.pathsep, oldPathEnv)
    os.environ['JAVA_HOME'] = "%s\jre" % (jdkDir)

    java_compile()
    generate_list_file()
    sys.exit(0)
