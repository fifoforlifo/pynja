import os
import inspect
import uuid
import importlib.machinery


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

rootDir = None

def set_root_dir(root_dir):
    global rootDir
    rootDir = root_dir

# Define global rootPaths object.
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
            pynja.import_dir("foo/thing")
        is equivalent to
            pynja.import_file("foo/thing/thing.py")
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
            pynja.import_subdir("foo/thing")
        is equivalent to
            pynja.import_subdir_file("foo/thing/thing.py")
    """
    basename = os.path.basename(subDir)
    subPath = os.path.join(subDir, basename + ".py")
    return import_subdir_file(subPath, altPath, callerDepth = 2)
