import os


def is_os_64bit():
    arch1 = (os.environ.get('PROCESSOR_ARCHITECTURE') or "").lower()
    arch2 = (os.environ.get('PROCESSOR_ARCHITEW6432') or "").lower()
    return (arch1 == "amd64" or arch2 == "amd64")


def set_msvc_environment(installDir, arch):
    oldPathEnv = os.environ.get('PATH') or ""

    os.environ["INCLUDE"] = "%s\\VC\\include" % installDir
    if arch == "x86":
        os.environ['LIB'] = "%s\\VC\\lib" % installDir
        os.environ['PATH'] = "%s\\VC\\bin;%s\\Common7\\IDE;%s" % (installDir, installDir, oldPathEnv)
    elif arch == "amd64":
        os.environ['LIB'] = "%s\\VC\\lib\\amd64" % installDir
        if is_os_64bit() and os.path.exists("%s\\VC\\bin\\amd64\\cl.exe" % installDir):
            os.environ['PATH'] = "%s\\VC\\bin\\amd64;%s\\Common7\\IDE;%s" % (installDir, installDir, oldPathEnv)
        else:
            os.environ['PATH'] = "%s\\VC\\bin\\x86_amd64;%s\\Common7\\IDE;%s" % (installDir, installDir, oldPathEnv)
    else:
        raise Exception("Unexpected arch ... should not be reachable ...")
