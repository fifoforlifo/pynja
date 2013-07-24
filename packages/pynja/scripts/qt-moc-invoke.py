import os
import sys
import re

script, qtBinDir, workingDir, sourcePath, outputPath, logPath, rspPath = sys.argv

os.chdir(workingDir)
outputDir = os.path.dirname(outputPath)
if not os.path.exists(outputDir):
    os.makedirs(outputDir)

oldPathEnv = os.environ['PATH']
os.environ['PATH'] = "%s%s%s" % (qtBinDir, os.pathsep, oldPathEnv)

cmd = "moc \"%s\" -o \"%s\" @\"%s\" 2>\"%s\"" % (sourcePath, outputPath, rspPath, logPath)
exitcode = os.system(cmd)
if exitcode:
    with open(logPath, "rt") as logFile:
        logContents = logFile.read()
        print("%s" % logContents)

sys.exit(exitcode)
