#!/usr/bin/python3.3
import sys
import os

rootDir = sys.path[0]
sys.path.append(os.path.normpath(os.path.join(rootDir, "..", "packages")))
sys.path.append(os.path.join(rootDir, "build"))

import pynja
import repo


build_cpp = True
build_java = True


def generate_ninja_build(projectMan):
    # define cpp_variants and toolchains on a per-OS basis
    cpp_variants = []
    java_variants = []
    deploy_variants = []

    isTargetWindows = (os.name == 'nt')

    if os.name == 'nt':
        if build_cpp:
            def toolchain_assign_winsdk(toolchain, msvcVer):
                if msvcVer < 10:
                    toolchain.winsdkVer = 71
                    toolchain.winsdkDir = pynja.rootPaths.winsdk71
                elif msvcVer < 14:
                    toolchain.winsdkVer = 80
                    toolchain.winsdkDir = pynja.rootPaths.winsdk80
                elif msvcVer == 14:
                    toolchain.winsdkVer = 81
                    toolchain.winsdkDir = pynja.rootPaths.winsdk81
                    toolchain.ucrtVer = pynja.rootPaths.ucrt100Ver
                    toolchain.ucrtDir = pynja.rootPaths.ucrt100
                else:
                    raise Exception('unsupported MSVC version')

            def make_msvc_tool_chain(msvcVer, installDir, arch):
                name = "msvc{msvcVer}-{arch}".format(**locals())
                toolchain = pynja.MsvcToolChain(name, installDir, arch, msvcVer)
                toolchain_assign_winsdk(toolchain, msvcVer)
                return toolchain

            def make_nvcc_tool_chain(nvccVer, nvccInstallDir, msvcVer, msvcInstallDir, arch):
                name = "nvcc{nvccVer}_msvc{msvcVer}-{arch}".format(**locals())
                if arch == 'x86':
                    nvccArch = "-m32"
                elif arch == 'amd64':
                    nvccArch = "-m64"
                else:
                    raise Exception('invalid arch %s' % (arch))
                toolchain = pynja.NvccToolChain(name, nvccInstallDir, "msvc%s" % msvcVer, msvcInstallDir, nvccArch, isTargetWindows)
                toolchain_assign_winsdk(toolchain, msvcVer)
                return toolchain

            if os.path.exists(pynja.rootPaths.msvc10):
                projectMan.add_toolchain(make_msvc_tool_chain(10, pynja.rootPaths.msvc10, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc10-x86-dbg-dcrt"))

                #projectMan.add_toolchain(make_nvcc_tool_chain(50, pynja.rootPaths.cuda50, 10, pynja.rootPaths.msvc10, "amd64"))
                #cpp_variants.append(repo.cpp.CppVariant("windows-msvc10-amd64-dbg-dcrt"))

                projectMan.add_toolchain(make_nvcc_tool_chain(50, pynja.rootPaths.cuda50, 10, pynja.rootPaths.msvc10, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-nvcc50_msvc10-x86-dbg-dcrt"))

            if os.path.exists(pynja.rootPaths.msvc11):
                projectMan.add_toolchain(make_msvc_tool_chain(11, pynja.rootPaths.msvc11, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc11-x86-dbg-dcrt"))

                projectMan.add_toolchain(make_msvc_tool_chain(11, pynja.rootPaths.msvc11, "amd64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc11-amd64-dbg-dcrt"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc11-amd64-rel-dcrt"))

                projectMan.add_toolchain(make_nvcc_tool_chain(50, pynja.rootPaths.cuda50, 11, pynja.rootPaths.msvc11, "amd64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-nvcc50_msvc11-amd64-dbg-dcrt"))

            if os.path.exists(pynja.rootPaths.msvc12):
                projectMan.add_toolchain(make_msvc_tool_chain(12, pynja.rootPaths.msvc12, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc12-x86-dbg-dcrt"))

                projectMan.add_toolchain(make_msvc_tool_chain(12, pynja.rootPaths.msvc12, "amd64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc12-amd64-dbg-dcrt"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc12-amd64-rel-dcrt"))

            if os.path.exists(pynja.rootPaths.msvc14):
                projectMan.add_toolchain(make_msvc_tool_chain(14, pynja.rootPaths.msvc14, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc14-x86-dbg-dcrt"))

                projectMan.add_toolchain(make_msvc_tool_chain(14, pynja.rootPaths.msvc14, "amd64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc14-amd64-dbg-dcrt"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc14-amd64-rel-dcrt"))

            if os.path.exists(pynja.rootPaths.mingw64):
                projectMan.add_toolchain(pynja.GccToolChain("mingw64-x86", pynja.rootPaths.mingw64, isTargetWindows))
                cpp_variants.append(repo.cpp.CppVariant("windows-mingw64-x86-dbg-dcrt"))

                projectMan.add_toolchain(pynja.GccToolChain("mingw64-amd64", pynja.rootPaths.mingw64, isTargetWindows))
                cpp_variants.append(repo.cpp.CppVariant("windows-mingw64-amd64-dbg-dcrt"))
                cpp_variants.append(repo.cpp.CppVariant("windows-mingw64-amd64-rel-dcrt"))

            if os.path.exists(pynja.rootPaths.android_ndk_r8d):
                projectMan.add_toolchain(pynja.AndroidGccToolChain("android_arm_gcc-aarch32", pynja.rootPaths.android_ndk_r8d, "4.7", 14, "armeabi", prefix="arm-linux-androideabi-"))
                cpp_variants.append(repo.cpp.CppVariant("android-android_arm_gcc-aarch32-dbg-dcrt"))

            projectMan.add_toolchain(pynja.qt.QtToolChain('qt5vc11', pynja.rootPaths.qt5vc11BinDir))

        if build_java:
            if os.path.exists(pynja.rootPaths.jdk15):
                projectMan.add_toolchain(pynja.JavacToolChain("javac", pynja.rootPaths.jdk15))
                java_variants.append(repo.java.JavaVariant("javac"))

    elif os.name == 'posix':
        if build_cpp:
            projectMan.add_toolchain(pynja.GccToolChain("gcc-x86", "/usr", isTargetWindows))
            cpp_variants.append(repo.cpp.CppVariant("linux-gcc-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.GccToolChain("gcc-amd64", "/usr", isTargetWindows))
            cpp_variants.append(repo.cpp.CppVariant("linux-gcc-amd64-dbg-dcrt"))

            projectMan.add_toolchain(pynja.ClangToolChain("clang-amd64", "/home/lolo/Downloads/clang+llvm-3.2-x86_64-linux-ubuntu-12.04", isTargetWindows))
            cpp_variants.append(repo.cpp.CppVariant("linux-clang-amd64-dbg-dcrt"))

        if build_java:
            if os.path.exists("/usr/bin/javac"):
                projectMan.add_toolchain(pynja.JavacToolChain("javac", "/usr/bin"))
                java_variants.append(repo.java.JavaVariant("javac"))

    else:
        raise Exception("Not implemented")

    deploy_variants.append(repo.DeployVariant("app32-dbg"))
    deploy_variants.append(repo.DeployVariant("app32-rel"))
    deploy_variants.append(repo.DeployVariant("app64-dbg"))
    deploy_variants.append(repo.DeployVariant("app64-rel"))

    # assume protoc is in the path
    projectMan.add_toolchain(pynja.protoc.ProtocToolChain("protoc"))
    # add re2c
    projectMan.add_toolchain(pynja.re2c.Re2cToolChain(pynja.rootPaths.re2c))

    projectMan.emit_rules()

    projectMan.ninjaFile.write("\n");
    projectMan.ninjaFile.write("#############################################\n");
    projectMan.ninjaFile.write("# Begin files.\n");
    projectMan.ninjaFile.write("\n");

    for variant in cpp_variants:
        projectMan.get_project("prog0", variant)
    for variant in java_variants:
        projectMan.get_project("java2", variant)
    for variant in deploy_variants:
        projectMan.get_project("test2", variant)

    currentScriptPath = os.path.join(pynja.rootDir, os.path.basename(__file__))

    projectMan.emit_deploy_targets()
    projectMan.emit_phony_targets()
    projectMan.emit_regenerator_target(currentScriptPath)



################################################################################
#   Main script

print("generating with rootDir=%s" % pynja.rootDir)
repo.init()
pynja.import_file('code/test2.py')
pynja.regenerate_build(generate_ninja_build, pynja.rootPaths.built, pynja.rootPaths.codeBrowsing)
