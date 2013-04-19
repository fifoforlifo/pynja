import os
import tempfile
from . import io
from . import build
from . import cb_vsproj

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

            if projectMan.emitVS2008Projects:
                cb_vsproj.VS2008.emit_vs_projects(projectMan)
            if projectMan.emitVS2010Projects:
                cb_vsproj.VS2010.emit_vs_projects(projectMan)
