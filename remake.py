#!/usr/bin/python3.3
import sys
import os

rootDir = sys.path[0]
sys.path.append(os.path.join(rootDir, "Build"))

import pynja
import repo


def get_current_script_path():
    if os.path.isabs(__file__):
        return __file__
    else:
        return os.path.join(repo.rootDir, __file__)


def generate_ninja_build(projectMan):
    # define variants and toolchains on a per-OS basis
    variants = []

    if os.name == 'nt':
        if os.path.exists(repo.rootPaths.msvc10):
            projectMan.add_toolchain(pynja.MsvcToolChain("msvc10-x86", repo.rootPaths.msvc10, "x86"))
            variants.append(repo.cpp.CppVariant("windows-msvc10-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.MsvcToolChain("msvc10-amd64", repo.rootPaths.msvc10, "amd64"))
            variants.append(repo.cpp.CppVariant("windows-msvc10-amd64-dbg-dcrt"))

            projectMan.add_toolchain(pynja.NvccToolChain("nvcc_msvc10-amd64", repo.rootPaths.cuda50, "msvc10", repo.rootPaths.msvc10, "-m64"))
            variants.append(repo.cpp.CppVariant("windows-nvcc_msvc10-amd64-dbg-dcrt"))

        if os.path.exists(repo.rootPaths.msvc11):
            projectMan.add_toolchain(pynja.MsvcToolChain("msvc11-x86", repo.rootPaths.msvc11, "x86"))
            variants.append(repo.cpp.CppVariant("windows-msvc11-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.MsvcToolChain("msvc11-amd64", repo.rootPaths.msvc11, "amd64"))
            variants.append(repo.cpp.CppVariant("windows-msvc11-amd64-dbg-dcrt"))

            projectMan.add_toolchain(pynja.NvccToolChain("nvcc_msvc11-amd64", repo.rootPaths.cuda50, "msvc10", repo.rootPaths.msvc10, "-m64"))
            variants.append(repo.cpp.CppVariant("windows-nvcc_msvc11-amd64-dbg-dcrt"))

        if os.path.exists(repo.rootPaths.mingw64):
            projectMan.add_toolchain(pynja.GccToolChain("mingw64-x86", repo.rootPaths.mingw64))
            variants.append(repo.cpp.CppVariant("windows-mingw64-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.GccToolChain("mingw64-amd64", repo.rootPaths.mingw64))
            variants.append(repo.cpp.CppVariant("windows-mingw64-amd64-dbg-dcrt"))
    elif os.name == 'posix':
        projectMan.add_toolchain(pynja.GccToolChain("gcc-x86", "/usr"))
        variants.append(repo.cpp.CppVariant("linux-gcc-x86-dbg-dcrt"))

        projectMan.add_toolchain(pynja.GccToolChain("gcc-amd64", "/usr"))
        variants.append(repo.cpp.CppVariant("linux-gcc-amd64-dbg-dcrt"))

        projectMan.add_toolchain(pynja.ClangToolChain("clang-amd64", "/home/lolo/Downloads/clang+llvm-3.2-x86_64-linux-ubuntu-12.04"))
        variants.append(repo.cpp.CppVariant("linux-clang-amd64-dbg-dcrt"))
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
    print("generating with rootDir=%s" % repo.rootDir)
    repo.rootPaths.init()
    pynja.regenerate_build(generate_ninja_build, repo.rootPaths.built)
