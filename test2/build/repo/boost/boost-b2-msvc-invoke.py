import os
import sys
import glob

script, boostDir, vcVer, vcDir, arch, runtimeLink, config, stageDir, logFilePath, guardFileBase, guardFilePath = sys.argv

# For this to work, modify tools\build\v2\tools\msvc.jam with this:
#
#   local rule auto-detect-toolset-versions ( )
#   {
#       # pynja: add explicit control of VC directory via environment variable PYNJA_VC_DIR
#       local pynja-vc-dir = os.environ PYNJA_VC_DIR ;
#       if $(version) && $(pynja-vc-dir)
#       {
#           register-configuration $(version) : [ $(pynja-vc-dir) ] ;
#           return $(version) ;
#       }
#
### Original code ...
#       if [ os.name ] in NT CYGWIN

if arch == "x86":
    addrModel = '32'
else:
    addrModel = '64'

os.chdir(boostDir)
os.environ["PYNJA_VC_DIR"] = vcDir

# extend this list with additional libs you wish to build
withLibs = "--with-thread --with-regex --with-filesystem"

cmdStatic = r'b2 --build-dir=built toolset=msvc-%(vcVer)s.0 link=static runtime-link=%(runtimeLink)s %(withLibs)s stage --stagedir="%(stageDir)s" -j 9 address-model=%(addrModel)s %(config)s  2>&1  >"%(logFilePath)s"' % locals()
cmdShared = r'b2 --build-dir=built toolset=msvc-%(vcVer)s.0 link=shared runtime-link=%(runtimeLink)s %(withLibs)s stage --stagedir="%(stageDir)s" -j 9 address-model=%(addrModel)s %(config)s  2>&1  >"%(logFilePath)s"' % locals()

if not os.path.exists(stageDir):
    os.makedirs(stageDir)

# erase old/stale guard files
for oldGuard in glob.glob(u'%(guardFileBase)s_*' % locals()):
    os.unlink(oldGuard)
# invoke boost build
exitcodeStatic = os.system(cmdStatic)
exitcodeShared = os.system(cmdShared)
if exitcodeStatic or exitcodeShared:
    sys.exit(1)

# success! create guard file
with open(guardFilePath, 'w+') as f:
    pass
sys.exit(0)
