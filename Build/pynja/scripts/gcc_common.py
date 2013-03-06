import os

def set_gcc_environment(installDir):
    oldPathEnv = os.environ.get('PATH') or ""
    os.environ['PATH'] = "%s/bin%s%s" % (installDir, os.pathsep, oldPathEnv)
    os.environ['INCLUDE'] = "%s/include" % installDir
    os.environ['LIB'] = "%s/lib" % installDir
