#!/usr/bin/python3.3
import sys
import os

rootDir = sys.path[0]
sys.path.append(os.path.join(rootDir, "Build"))

import pynja
import upynja


def get_current_script_path():
    if os.path.isabs(__file__):
        return __file__
    else:
        return os.path.join(upynja.rootDir, __file__)


def generate_ninja_build(projectMan):
    # define variants and toolchains on a per-OS basis
    variants = []

    if os.name == 'nt':
        if os.path.exists(upynja.rootPaths.msvc10):
            projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc10-x86", upynja.rootPaths.msvc10, "x86"))
            variants.append(upynja.cpp.CppVariant("windows-msvc10-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc10-amd64", upynja.rootPaths.msvc10, "amd64"))
            variants.append(upynja.cpp.CppVariant("windows-msvc10-amd64-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.NvccToolChain("nvcc_msvc10-amd64", upynja.rootPaths.cuda50, "msvc10", upynja.rootPaths.msvc10, "-m64"))
            variants.append(upynja.cpp.CppVariant("windows-nvcc_msvc10-amd64-dbg-dcrt"))

        if os.path.exists(upynja.rootPaths.msvc11):
            projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc11-x86", upynja.rootPaths.msvc11, "x86"))
            variants.append(upynja.cpp.CppVariant("windows-msvc11-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc11-amd64", upynja.rootPaths.msvc11, "amd64"))
            variants.append(upynja.cpp.CppVariant("windows-msvc11-amd64-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.NvccToolChain("nvcc_msvc11-amd64", upynja.rootPaths.cuda50, "msvc10", upynja.rootPaths.msvc10, "-m64"))
            variants.append(upynja.cpp.CppVariant("windows-nvcc_msvc11-amd64-dbg-dcrt"))

        if os.path.exists(upynja.rootPaths.mingw64):
            projectMan.add_toolchain(pynja.tc.GccToolChain("mingw64-x86", upynja.rootPaths.mingw64))
            variants.append(upynja.cpp.CppVariant("windows-mingw64-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.GccToolChain("mingw64-amd64", upynja.rootPaths.mingw64))
            variants.append(upynja.cpp.CppVariant("windows-mingw64-amd64-dbg-dcrt"))
    elif os.name == 'posix':
        projectMan.add_toolchain(pynja.tc.GccToolChain("gcc-x86", "/usr"))
        variants.append(upynja.cpp.CppVariant("linux-gcc-x86-dbg-dcrt"))

        projectMan.add_toolchain(pynja.tc.GccToolChain("gcc-amd64", "/usr"))
        variants.append(upynja.cpp.CppVariant("linux-gcc-amd64-dbg-dcrt"))
    else:
        raise Exception("Not implemented")

    projectMan.emit_rules()

    projectMan.ninjaFile.write("\n");
    projectMan.ninjaFile.write("#############################################\n");
    projectMan.ninjaFile.write("# Begin files.\n");
    projectMan.ninjaFile.write("\n");

    for variant in variants:
        projectMan.get_project("Prog0", variant)

    projectMan.emit_phony_targets()

    projectMan.emit_regenerator_target(get_current_script_path())



if (__name__ == "__main__"):
    print("generating with rootDir=%s" % upynja.rootDir)
    pynja.build.regenerate_build(generate_ninja_build, upynja.rootPaths.built)
