import os
import sys
import re

script, workingDir, jdkDir, outputPath, logPath = sys.argv


os.chdir(workingDir)
outputDir = os.path.dirname(outputPath)
if not os.path.exists(outputDir):
    os.makedirs(outputDir)
oldPathEnv = os.environ['PATH']
os.environ['PATH'] = "%s%sbin%s%s" % (jdkDir, os.sep, os.pathsep, oldPathEnv)
os.environ['JAVA_HOME'] = "%s\jre" % (jdkDir)

cmd = "jar cvf \"%s\" * > \"%s\" 2>&1" % (outputPath, logPath)
exitcode = os.system(cmd)
with open(logPath, "rt") as logFile:
    logContents = logFile.read()
if re.search("warning:|error:", logContents, re.MULTILINE):
    print("%s" % logContents)

sys.exit(exitcode)
