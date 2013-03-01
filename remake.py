import sys
import os
import tempfile

rootDir = sys.path[0]
sys.path.append(os.path.join(rootDir, "Build"))

import pynja
import upynja


def generate_ninja_build(ninjaFile, ninjaPath):
    projectMan = pynja.build.ProjectMan(ninjaFile, ninjaPath)

    # define variants and toolchains on a per-OS basis
    variants = []

    if os.name == 'nt':
        if os.path.exists(upynja.rootPaths.msvc10):
            projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc10-x86", upynja.rootPaths.msvc10, "x86"))
            variants.append(upynja.cpp.CppVariant("windows-msvc10-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc10-amd64", upynja.rootPaths.msvc10, "amd64"))
            variants.append(upynja.cpp.CppVariant("windows-msvc10-amd64-dbg-dcrt"))

        if os.path.exists(upynja.rootPaths.mingw64):
            projectMan.add_toolchain(pynja.tc.GccToolChain("mingw64-x86", upynja.rootPaths.mingw64))
            variants.append(upynja.cpp.CppVariant("windows-mingw64-x86-dbg-dcrt"))

            projectMan.add_toolchain(pynja.tc.GccToolChain("mingw64-amd64", upynja.rootPaths.mingw64))
            variants.append(upynja.cpp.CppVariant("windows-mingw64-amd64-dbg-dcrt"))

    else:
        raise NotImplemented()

    projectMan.emit_rules()

    ninjaFile.write("\n");
    ninjaFile.write("#############################################\n");
    ninjaFile.write("# Begin files.\n");
    ninjaFile.write("\n");

    for variant in variants:
        projectMan.get_project("Prog0", variant)

    projectMan.emit_phony_targets()

    projectMan.emit_regenerator_target(__file__)


def regenerate_build():
    builtDir = upynja.rootPaths.built
    ninjaPath = os.path.join(builtDir, "build.ninja")
    lockPath = ninjaPath + ".lock"

    pynja.io.create_dir(builtDir)

    with pynja.io.CrudeLockFile(lockPath):
        with tempfile.TemporaryFile('w+t') as tempNinjaFile:
            generate_ninja_build(tempNinjaFile, ninjaPath)
            tempNinjaFile.seek(0)
            newContent = tempNinjaFile.read()
            oldContent = ""
            if os.path.exists(ninjaPath):
                with open(ninjaPath, "rt") as ninjaFile:
                    oldContent = ninjaFile.read()
            if newContent != oldContent:
                with open(ninjaPath, "wt") as ninjaFile:
                    ninjaFile.write(newContent)


if (__name__ == "__main__"):
    print("generating with rootDir=%s" % upynja.rootDir)
    regenerate_build()
