# declarations in this file are imported into the repo namespace

import sys
import os
import inspect
import uuid
import importlib.machinery

import pynja
from .root_dir import finder

################################################################################
#   There's a lot of extra book-keeping in some areas to work around the fact that
#   Python <3.4 don't consistently provide __file__ as an absolute path.
#
#   Specifically, in these prior versions, the sys.path entry that was used
#   to load the source file dictates the __file__ prefix.  If that entry was relative,
#   the source file's __file__ is also relative.
#
#   cf. http://stackoverflow.com/questions/7116889/python-file-attribute-absolute-or-relative

################################################################################
#   Script loading

_scriptPathsRel = {}            # map [uuid4] name -> relative path for script files
_scriptPathsAbs = {}            # map [uuid4] name -> absolute path for script files
_scriptRelToAbs = {}            # map relPath -> absPath for script files

def _import_script(name, absPath):
    absPath = os.path.normpath(absPath)
    if not os.path.isabs(absPath):
        raise Exception("expected absolute path, but absPath=%s" % (absPath))
    loader = importlib.machinery.SourceFileLoader(name, absPath)
    return loader.load_module(name)

################################################################################
#   rootPaths management

rootDir = finder.get_root_dir()

# Define a singleton rootPaths object.
class RootPaths(object):
    pass

rootPathsAbs = RootPaths()      # map project name -> absolute path
rootPathsRel = RootPaths()      # map project name -> relative path from rootDir
rootPaths = rootPathsAbs        # shorter alias for rootPathsAbs


def _add_project_entry(projName, scriptName):
    """Add project to rootPathsRel and rootPathAbs.

        Keyword arguments
        projName -- __name__ of the project class
        scriptName -- __name__ of the script in which the project class was defined
    """
    relPath = os.path.dirname(_scriptPathsRel[scriptName])
    absPath = os.path.dirname(_scriptPathsAbs[scriptName])
    oldAbsPath = getattr(rootPaths, projName, None)
    if oldAbsPath:
        if oldAbsPath == absPath:
            return
        raise Exception("Attempting to add duplicate project '%s' from:\n    %s\n    %s" % (name, oldAbsPath, absPath))
    setattr(rootPathsAbs, projName, absPath)
    setattr(rootPathsRel, projName, relPath)


def import_repo_file(relPathFromRootDir, altPath = None):
    """Import a file by relative-path-from-repo-rootDir; supports micro-branching.

        Keyword arguments
        relPathFromRootDir -- relative path from rootDir; this is the default un-microbranched location of the project file
        altPath -- absolute path, may be None; only needed for microbranching
    """
    if os.path.isabs(relPathFromRootDir):
        raise Exception("relPathFromRootDir must not be absolute: %s" % (relPathFromRootDir))

    relPath = os.path.normpath(relPathFromRootDir)
    absPath = altPath
    if not absPath:
        absPath = os.path.normpath(os.path.join(rootDir, relPath))

    if relPath in _scriptRelToAbs:
        oldAbsPath = _scriptRelToAbs[relPath]
        if oldAbsPath != absPath:
            raise Exception("Attempting to import same project_file with differing absPath:\n    %s\n    %s" % (oldAbsPath, absPath))
        return

    name = str(uuid.uuid4())
    _scriptPathsAbs[name] = absPath
    _scriptPathsRel[name] = relPath
    _scriptRelToAbs[relPath] = absPath

    return _import_script(name, absPath)


def import_repo_dir(relDirFromRootDir, altPath = None):
    """Call import_repo_file with the .py file whose name matches relDirFromRootDir."""
    basename = os.path.basename(relDirFromRootDir)
    relPathFromRootDir = os.path.join(relDirFromRootDir, basename + ".py")
    return import_repo_file(relPathFromRootDir, altPath)


def import_subdir_file(subPath, callerDepth = 1):
    """Import a file by relative-path-from-invoking-script-dir; does not support micro-branching.

        Keyword arguments
        subdirPath -- filename, as relative path from invoking file's directory

        subdirPath must be a nested subdirectory.  You may not "reach outside"
        to a sibling or parent directory.  If you need to do this, consider
        one of these alternatives:

        *   importing from a parent directory's script
        *   defining a rootPath and calling import_project_file() instead.
    """
    frame = inspect.stack()[callerDepth]
    module = inspect.getmodule(frame[0])

    subPath = os.path.normpath(subPath)
    if len(subPath) > 3 and subPath[0] == '.' and subPath[1] == '.' and subPath[2] == os.path.sep:
        raise Exception("you may not reach outside your directory: %s" % (subPath))

    relPath = _scriptPathsRel[module.__name__]
    absPath = _scriptPathsAbs[module.__name__]
    relPath = os.path.join(os.path.dirname(relPath), subPath)
    absPath = os.path.join(os.path.dirname(absPath), subPath)

    name = str(uuid.uuid4())
    _scriptPathsAbs[name] = absPath
    _scriptPathsRel[name] = relPath
    _scriptRelToAbs[relPath] = absPath

    return _import_script(name, absPath)


def import_subdir(subDir):
    """Call import_subdir_file with the .py file whose name matches subDir."""
    basename = os.path.basename(subDir)
    subPath = os.path.join(subDir, basename + ".py")
    return import_subdir_file(subPath, callerDepth = 2)


def init():
    # qt helper projects
    import_repo_file('build/repo/qt/qt_core.py')
    import_repo_file('build/repo/qt/qt_xml.py')
    # boost helper projects
    import_repo_file('build/repo/boost/boost_build.py')
    # real source projects
    import_repo_file('code/test2.py')
    import_repo_dir('code/a')
    import_repo_dir('code/prog0')
    import_repo_dir('code/java1')
    import_repo_dir('code/java2')
    import_repo_dir('code/qt0')

    # additional build/source paths
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
