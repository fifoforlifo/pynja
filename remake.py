import sys
import os
import tempfile

rootDir = sys.path[0]
sys.path.append(os.path.join(rootDir, "Build"))

import pynja
import upynja


def generate_ninja_build(ninjaFile):
    projectMan = pynja.build.ProjectMan(ninjaFile)

    # define variants and toolchains on a per-OS basis
    variants = []

    if os.name == 'nt':
        variants.append(upynja.cpp.CppVariant("windows-msvc10-x86-dbg-dcrt"))
        variants.append(upynja.cpp.CppVariant("windows-msvc10-amd64-dbg-dcrt"))

        projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc10-x86", upynja.rootPaths.msvc10, "x86"))
        projectMan.add_toolchain(pynja.tc.MsvcToolChain("msvc10-amd64", upynja.rootPaths.msvc10, "amd64"))

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


def regenerate_build():
    builtDir = upynja.rootPaths.built
    ninjaPath = os.path.join(builtDir, "build.ninja")
    lockPath = ninjaPath + ".lock"

    pynja.io.create_dir(builtDir)

    with pynja.io.CrudeLockFile(lockPath):
        with tempfile.TemporaryFile('w+t') as tempNinjaFile:
            generate_ninja_build(tempNinjaFile)
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
