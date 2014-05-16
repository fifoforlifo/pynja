# declarations in this file are imported into the repo namespace

import sys
import os
import inspect
import pynja
from .root_dir import finder

## note: There's a lot of extra book-keeping in some areas because
##       Python <3.4 don't consistently provide __file__ as an abs. path.

rootDir = finder.get_root_dir()

# Define a singleton rootPaths object.
class RootPaths(object):
    pass
rootPathsAbs = RootPaths()      # absolute paths
rootPathsRel = RootPaths()      # relative paths from the repo
rootPaths = rootPathsAbs        # shorter alias

subdirPathsAbs = RootPaths()    # for impoort_root_paths


def add_project_file(name, relPath, absPath = None, doImport = True):
    """ Add rootPath.<name> and optionally __import__(name)

        Keyword arguments
        name = name of file to be imported, and the "primary" project class
        relPath = relative path from rootDir; this is the default un-microbranched location of the project file
        absPath = absolute path, may be None; only needed for microbranching
    """
    if not absPath:
        absPath = os.path.normpath(os.path.join(rootDir, relPath))
    existingAbsPath = getattr(rootPaths, name, None)
    if existingAbsPath:
        if existingAbsPath == absPath:
            return
        raise Exception("Attempting to add duplicate project '%s' from:\n    %s\n    %s" % (name, existingAbsPath, absPath))
    setattr(rootPathsAbs, name, absPath)
    setattr(rootPathsRel, name, os.path.normpath(relPath))
    if doImport:
        if absPath not in sys.path: # O(N) check, but this is low-frequency code
            sys.path.append(absPath)
        __import__(name)
        # now all decorated project classes from the imported module will be available


# Adds a project file by subdirectory path, relative to the invoking file's directory.
# Most often called from a file imported by add_repo_subdirectory.
def add_project_file_in_subdir(name, subdirPath):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    parentName = module.__name__
    relPath = os.path.join(getattr(rootPathsRel, parentName), subdirPath)
    absPath = os.path.join(getattr(rootPathsAbs, parentName, None), subdirPath)
    add_project_file(name, relPath, absPath)


# Add a script in a subdirectory, that can contribute additional project definitions.
# This allows modularizing the repository, where each subdirectory manages its own components.
# This function is somewhat analagous to a CMake add_subdirectory.
def add_repo_subdirectory(name, relPath, absPath = None):
    if not absPath:
        absPath = os.path.normpath(os.path.join(rootDir, relPath))
    if absPath not in sys.path: # O(N) check, but this is low-frequency code
        sys.path.append(absPath)
    setattr(rootPathsAbs, name, absPath)
    setattr(rootPathsRel, name, os.path.normpath(relPath))
    submodule = __import__(name)
    submodule.add_root_paths()


def init():
    # qt helper projects
    add_project_file("qt_core", "build/repo/qt")
    add_project_file("qt_xml", "build/repo/qt")
    # boost helper projects
    add_project_file("boost_build", "build/repo/boost")
    # real source projects
    add_project_file("test2", "code")
    add_repo_subdirectory("subdir_a", "code/a")
    add_project_file("prog0", "code/prog0")
    add_project_file("java1", "code/java1")
    add_project_file("java2", "code/java2")
    add_project_file("qt0", "code/qt0")

    rootPaths.dllexport = os.path.join(rootDir, "code/dllexport")

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
