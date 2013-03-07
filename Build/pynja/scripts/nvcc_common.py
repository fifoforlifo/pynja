import os
import sys


def set_nvcc_environment(installDir, hostCompiler, hostInstallDir, addressModel):
    oldPathEnv = os.environ.get('PATH') or ""
    if os.name == 'nt':
        os.environ['PATH'] = "%s\\bin%s%s" % (installDir, os.pathsep, oldPathEnv)
    else:
        os.environ['PATH'] = "%s/bin%s%s" % (installDir, os.pathsep, oldPathEnv)

    if "gcc" in hostCompiler:
        import gcc_common
        gcc_common.set_gcc_environment(hostInstallDir)
    else:
        import msvc_common
        arch = "x86" if addressModel == "-m32" else "amd64"
        msvc_common.set_msvc_environment(hostInstallDir, arch)


def escape_path(path):
    return path.replace("\\", "/")


def calc_msvc_options(hostCompiler):
    if hostCompiler == "msvc8":
        vsver = 2005
    elif hostCompiler == "msvc9":
        vsver = 2008
    elif hostCompiler == "msvc10":
        vsver = 2010
    else:
        raise Exception("Unsupported msvc version: %s" % hostCompiler)

    forceCompilerOption = "--use-local-env --cl-version=%s" % vsver
    return forceCompilerOption
