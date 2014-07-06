# declarations in this file are imported into the repo namespace

import sys
import os
import pynja
from .root_dir import finder


pynja.set_root_dir(finder.get_root_dir())
pynja.rootDir = pynja.root_paths.rootDir


def init():
    # qt helper projects
    pynja.import_file('build/repo/qt/qt_core.py')
    pynja.import_file('build/repo/qt/qt_xml.py')
    # boost helper projects
    pynja.import_file('build/repo/boost/boost_build.py')

    # output paths
    pynja.rootPaths.out = os.path.join(pynja.rootDir, "_out")
    pynja.rootPaths.built = os.path.join(pynja.rootPaths.out, "built")
    pynja.rootPaths.codeBrowsing = os.path.join(pynja.rootPaths.out, "cb")
    pynja.rootPaths.bin = os.path.join(pynja.rootPaths.out, "bin")

    # tool paths
    pynja.rootPaths.protobuf = os.path.join(pynja.rootDir, "imports/protobuf-2.4.1")

    if (os.name == 'nt'):
        # you can customize these paths to point at a location in source control
        if pynja.io.is_64bit_os():
            pynja.rootPaths.msvc9 = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0"
            pynja.rootPaths.msvc10 = r"C:\Program Files (x86)\Microsoft Visual Studio 10.0"
            pynja.rootPaths.msvc11 = r"C:\Program Files (x86)\Microsoft Visual Studio 11.0"
        else:
            pynja.rootPaths.msvc9 = r"C:\Program Files\Microsoft Visual Studio 9.0"
            pynja.rootPaths.msvc10 = r"C:\Program Files\Microsoft Visual Studio 10.0"
            pynja.rootPaths.msvc11 = r"C:\Program Files\Microsoft Visual Studio 11.0"

        pynja.rootPaths.winsdk71 = r'C:\Program Files\Microsoft SDKs\Windows\v7.1';
        pynja.rootPaths.winsdk80 = r'C:\Program Files (x86)\Windows Kits\8.0';

        pynja.rootPaths.mingw = r"C:\MinGW"
        pynja.rootPaths.mingw64 = r"C:\MinGW64"

        pynja.rootPaths.cuda50 = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v5.0"

        pynja.rootPaths.jdk15 = r"C:\Program Files\Java\jdk1.7.0_15"

        pynja.rootPaths.qt5vc11BinDir = r"C:\Qt\Qt5.0.2\5.0.2\msvc2012_64\bin"
        pynja.rootPaths.boost150 = r"D:\work\code\boost\boost_1_50_0"
        pynja.rootPaths.re2c = os.path.join(pynja.rootDir, r"prebuilt\windows\re2c\re2c-0.13.5-bin\re2c.exe")
