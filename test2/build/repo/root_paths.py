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

    Args:
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


def import_file(relPathFromRootDir, altPath = None):
    """Import a file by relative-path-from-repo-rootDir.

    Args:
        relPathFromRootDir -- relative path from rootDir; this is the default un-microbranched location of the project file
        altPath -- alternate absolute path to the file; defaults to None.
            Specify this for local (temporary) microbranching.
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


def import_dir(relDirFromRootDir, altPath = None):
    """Call import_file with the .py file whose name matches relDirFromRootDir.

    Example:
            repo.import_dir("foo/thing")
        is equivalent to
            repo.import_file("foo/thing/thing.py")
    """
    basename = os.path.basename(relDirFromRootDir)
    relPathFromRootDir = os.path.join(relDirFromRootDir, basename + ".py")
    return import_file(relPathFromRootDir, altPath)


def import_subdir_file(subPath, altPath = None, callerDepth = 1):
    """Import a file by relative-path-from-invoking-script-dir.

    Args:
        subdirPath -- filename, as relative path from invoking file's directory
        altPath -- alternate absolute path to the file; defaults to None.
            This path sepcifies a microbranch location.

    subdirPath must be a nested subdirectory.  You may not "reach outside"
    to a sibling or parent directory; permitting that would break modularity.
    If you need to do this, consider one of these alternatives:

    *   calling import_subdir_file from a parent directory's script
    *   defining a rootPath and calling import_file() instead.
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


def import_subdir(subDir, altPath = None):
    """Call import_subdir_file with the .py file whose name matches subDir.

    Example:
            repo.import_subdir("foo/thing")
        is equivalent to
            repo.import_subdir_file("foo/thing/thing.py")
    """
    basename = os.path.basename(subDir)
    subPath = os.path.join(subDir, basename + ".py")
    return import_subdir_file(subPath, altPath, callerDepth = 2)


def init():
    # define repo variable for consistent usage syntax with all other build scripts
    repo = sys.modules[__name__]
    # qt helper projects
    repo.import_file('build/repo/qt/qt_core.py')
    repo.import_file('build/repo/qt/qt_xml.py')
    # boost helper projects
    repo.import_file('build/repo/boost/boost_build.py')

    # output paths
    repo.rootPaths.out = os.path.join(repo.rootDir, "_out")
    repo.rootPaths.built = os.path.join(repo.rootPaths.out, "built")
    repo.rootPaths.codeBrowsing = os.path.join(repo.rootPaths.out, "cb")
    repo.rootPaths.bin = os.path.join(repo.rootPaths.out, "bin")

    # tool paths
    repo.rootPaths.protobuf = os.path.join(repo.rootDir, "imports/protobuf-2.4.1")

    if (os.name == 'nt'):
        # you can customize these paths to point at a location in source control
        if pynja.io.is_64bit_os():
            repo.rootPaths.msvc9 = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0"
            repo.rootPaths.msvc10 = r"C:\Program Files (x86)\Microsoft Visual Studio 10.0"
            repo.rootPaths.msvc11 = r"C:\Program Files (x86)\Microsoft Visual Studio 11.0"
        else:
            repo.rootPaths.msvc9 = r"C:\Program Files\Microsoft Visual Studio 9.0"
            repo.rootPaths.msvc10 = r"C:\Program Files\Microsoft Visual Studio 10.0"
            repo.rootPaths.msvc11 = r"C:\Program Files\Microsoft Visual Studio 11.0"

        repo.rootPaths.winsdk71 = r'C:\Program Files\Microsoft SDKs\Windows\v7.1';
        repo.rootPaths.winsdk80 = r'C:\Program Files (x86)\Windows Kits\8.0';

        repo.rootPaths.mingw = r"C:\MinGW"
        repo.rootPaths.mingw64 = r"C:\MinGW64"

        repo.rootPaths.cuda50 = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v5.0"

        repo.rootPaths.jdk15 = r"C:\Program Files\Java\jdk1.7.0_15"

        repo.rootPaths.qt5vc11BinDir = r"C:\Qt\Qt5.0.2\5.0.2\msvc2012_64\bin"
        repo.rootPaths.boost150 = r"D:\work\code\boost\boost_1_50_0"
        repo.rootPaths.re2c = os.path.join(rootDir, r"prebuilt\windows\re2c\re2c-0.13.5-bin\re2c.exe")
