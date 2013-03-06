# declarations in this file are imported into the upynja namespace

import sys
import os
import pynja
import upynja.root_dir.finder


class RootPaths(object):
    pass


rootDir = upynja.root_dir.finder.get_root_dir()
rootPaths = RootPaths()


def add_project_dir(name, relPath, absPath = None):
    """Add a rootPath and import it."""
    if not absPath:
        absPath = os.path.normpath(os.path.join(rootDir, relPath))
    setattr(rootPaths, name, absPath)
    setattr(rootPaths, name + "_rel", os.path.normpath(relPath))
    sys.path.append(absPath)
    __import__(name)


add_project_dir("A0", "Modules/A0")
add_project_dir("A1", "Modules/A1")
add_project_dir("Prog0", "Modules/Prog0")

rootPaths.built = os.path.join(rootDir, "Built")

if (os.name == 'nt'):
    # you can customize these paths to point at a location in source control
    if pynja.io.is_64bit_os():
        rootPaths.msvc9 = "C:\\Program Files (x86)\\Microsoft Visual Studio 9.0"
        rootPaths.msvc10 = "C:\\Program Files (x86)\\Microsoft Visual Studio 10.0"
        rootPaths.msvc11 = "C:\\Program Files (x86)\\Microsoft Visual Studio 11.0"
    else:
        rootPaths.msvc9 = "C:\\Program Files\\Microsoft Visual Studio 9.0"
        rootPaths.msvc10 = "C:\\Program Files\\Microsoft Visual Studio 10.0"
        rootPaths.msvc11 = "C:\\Program Files\\Microsoft Visual Studio 11.0"

    rootPaths.winsdk71 = 'C:\\Program Files\\Microsoft SDKs\\Windows\\v7.1';
    rootPaths.winsdk80 = 'C:\\Program Files (x86)\\Windows Kits\\8.0';

    rootPaths.mingw = "C:\\MinGW"
    rootPaths.mingw64 = "C:\\MinGW64"
