# declarations in this file are imported into the repo namespace

import sys
import os
import pynja
from .root_dir import finder

rootDir = finder.get_root_dir()

def add_project_dir(name, relPath, absPath = None):
    """Add a rootPath and import it."""
    if not absPath:
        absPath = os.path.normpath(os.path.join(rootDir, relPath))
    setattr(rootPaths, name, absPath)
    setattr(rootPaths, name + "_rel", os.path.normpath(relPath))
    sys.path.append(absPath)
    __import__(name)

class RootPaths(object):
    def init(self):
        # qt helper projects
        add_project_dir("qt_core", "build/repo/qt")
        add_project_dir("qt_xml", "build/repo/qt")
        # boost helper projects
        add_project_dir("boost_build", "build/repo/boost")
        # real source projects
        add_project_dir("test2", "code")
        add_project_dir("a0", "code/a0")
        add_project_dir("a1", "code/a1")
        add_project_dir("a2", "code/a2")
        add_project_dir("prog0", "code/prog0")
        add_project_dir("java1", "code/java1")
        add_project_dir("java2", "code/java2")
        add_project_dir("qt0", "code/qt0")

        # output paths
        rootPaths.out = os.path.join(rootDir, "_out")
        rootPaths.built = os.path.join(rootPaths.out, "built")
        rootPaths.codeBrowsing = os.path.join(rootPaths.out, "cb")
        rootPaths.bin = os.path.join(rootPaths.out, "bin")

        # tool paths
        rootPaths.protobuf = os.path.join(rootDir, "imports/protobuf-2.4.1")

        if (os.name == 'nt'):
            # you can customize these paths to point at a location in source control
            if pynja.io.is_64bit_os():
                rootPaths.msvc9 = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0"
                rootPaths.msvc10 = r"C:\Program Files (x86)\Microsoft Visual Studio 10.0"
                rootPaths.msvc11 = r"C:\Program Files (x86)\Microsoft Visual Studio 11.0"
            else:
                rootPaths.msvc9 = r"C:\Program Files\Microsoft Visual Studio 9.0"
                rootPaths.msvc10 = r"C:\Program Files\Microsoft Visual Studio 10.0"
                rootPaths.msvc11 = r"C:\Program Files\Microsoft Visual Studio 11.0"

            rootPaths.winsdk71 = r'C:\Program Files\Microsoft SDKs\Windows\v7.1';
            rootPaths.winsdk80 = r'C:\Program Files (x86)\Windows Kits\8.0';

            rootPaths.mingw = r"C:\MinGW"
            rootPaths.mingw64 = r"C:\MinGW64"

            rootPaths.cuda50 = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v5.0"

            rootPaths.jdk15 = r"C:\Program Files\Java\jdk1.7.0_15"

            rootPaths.qt5vc11BinDir = r"C:\Qt\Qt5.0.2\5.0.2\msvc2012_64\bin"
            rootPaths.boost150 = r"D:\work\code\boost\boost_1_50_0"
            rootPaths.re2c = os.path.join(rootDir, r"prebuilt\windows\re2c\re2c-0.13.5-bin\re2c.exe")


rootPaths = RootPaths()
