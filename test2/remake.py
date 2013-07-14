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


def get_current_script_path():
    if os.path.isabs(__file__):
        return __file__
    else:
        return os.path.join(repo.rootDir, __file__)


def generate_ninja_build(projectMan):
    # define cpp_variants and toolchains on a per-OS basis
    cpp_variants = []
    java_variants = []

    if os.name == 'nt':
        if build_cpp:
            if os.path.exists(repo.rootPaths.msvc10):
                projectMan.add_toolchain(pynja.MsvcToolChain("msvc10-x86", repo.rootPaths.msvc10, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc10-x86-dbg-dcrt"))

                projectMan.add_toolchain(pynja.MsvcToolChain("msvc10-amd64", repo.rootPaths.msvc10, "amd64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc10-amd64-dbg-dcrt"))

                projectMan.add_toolchain(pynja.NvccToolChain("nvcc_msvc10-amd64", repo.rootPaths.cuda50, "msvc10", repo.rootPaths.msvc10, "-m64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-nvcc_msvc10-amd64-dbg-dcrt"))

            if os.path.exists(repo.rootPaths.msvc11):
                projectMan.add_toolchain(pynja.MsvcToolChain("msvc11-x86", repo.rootPaths.msvc11, "x86"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc11-x86-dbg-dcrt"))

                projectMan.add_toolchain(pynja.MsvcToolChain("msvc11-amd64", repo.rootPaths.msvc11, "amd64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc11-amd64-dbg-dcrt"))
                cpp_variants.append(repo.cpp.CppVariant("windows-msvc11-amd64-rel-dcrt"))

                projectMan.add_toolchain(pynja.NvccToolChain("nvcc_msvc11-amd64", repo.rootPaths.cuda50, "msvc10", repo.rootPaths.msvc10, "-m64"))
                cpp_variants.append(repo.cpp.CppVariant("windows-nvcc_msvc11-amd64-dbg-dcrt"))

            if os.path.exists(repo.rootPaths.mingw64):
                projectMan.add_toolchain(pynja.GccToolChain("mingw64-x86", repo.rootPaths.mingw64))
                cpp_variants.append(repo.cpp.CppVariant("windows-mingw64-x86-dbg-dcrt"))

                projectMan.add_toolchain(pynja.GccToolChain("mingw64-amd64", repo.rootPaths.mingw64))
                cpp_variants.append(repo.cpp.CppVariant("windows-mingw64-amd64-dbg-dcrt"))
                cpp_variants.append(repo.cpp.CppVariant("windows-mingw64-amd64-rel-dcrt"))

        if build_java:
            if os.path.exists(repo.rootPaths.jdk15):
                projectMan.add_toolchain(pynja.JavacToolChain("javac", repo.rootPaths.jdk15))
                java_variants.append(repo.java.JavaVariant("javac"))

    elif os.name == 'posix':
        if build_cpp:
            projectMan.add_toolchain(pynja.GccToolChain("gcc-x86", "/usr"))
            cpp_variants.append(repo.cpp.CppVariant("linux-gcc-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.GccToolChain("gcc-amd64", "/usr"))
            cpp_variants.append(repo.cpp.CppVariant("linux-gcc-amd64-dbg-dcrt"))

            projectMan.add_toolchain(pynja.ClangToolChain("clang-amd64", "/home/lolo/Downloads/clang+llvm-3.2-x86_64-linux-ubuntu-12.04"))
            cpp_variants.append(repo.cpp.CppVariant("linux-clang-amd64-dbg-dcrt"))

        if build_java:
            if os.path.exists("/usr/bin/javac"):
                projectMan.add_toolchain(pynja.JavacToolChain("javac", "/usr/bin"))
                java_variants.append(repo.java.JavaVariant("javac"))

    else:
        raise Exception("Not implemented")

    projectMan.add_toolchain(repo.protocToolChain)
    projectMan.emit_rules()

    projectMan.ninjaFile.write("\n");
    projectMan.ninjaFile.write("#############################################\n");
    projectMan.ninjaFile.write("# Begin files.\n");
    projectMan.ninjaFile.write("\n");

    for variant in cpp_variants:
        projectMan.get_project("prog0", variant)
    for variant in java_variants:
        projectMan.get_project("java2", variant)


    projectMan.emit_phony_targets()
    projectMan.emit_regenerator_target(get_current_script_path())



if (__name__ == "__main__"):
    print("generating with rootDir=%s" % repo.rootDir)
    repo.rootPaths.init()
    pynja.regenerate_build(generate_ninja_build, repo.rootPaths.built, repo.rootPaths.codeBrowsing)
