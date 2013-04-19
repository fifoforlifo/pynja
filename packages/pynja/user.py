import os
import tempfile
from . import io
from . import build
from . import vsproj

def regenerate_build(generate_ninja_build, builtDir):
    ninjaPath = os.path.join(builtDir, "build.ninja")
    lockPath = ninjaPath + ".lock"

    io.create_dir(builtDir)

    with io.CrudeLockFile(lockPath):
        with tempfile.TemporaryFile('w+t') as tempNinjaFile:
            projectMan = build.ProjectMan(tempNinjaFile, ninjaPath)
            generate_ninja_build(projectMan)
            tempNinjaFile.seek(0)
            newContent = tempNinjaFile.read()
            io.write_file_if_different(ninjaPath, newContent)
            vsproj.VS2008.emit_vs_projects(projectMan)
