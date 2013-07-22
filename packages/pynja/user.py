import os
import tempfile
from . import io
from . import build
from . import cb_vsproj

def regenerate_build(generate_ninja_build, builtDir, codeBrowsingDir = None):
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

            if os.name == 'nt':
                generators = []
                generators.append(cb_vsproj.VS2008(projectMan, codeBrowsingDir))
                generators.append(cb_vsproj.VS2010(projectMan, codeBrowsingDir))
                generators.append(cb_vsproj.VS2012(projectMan, codeBrowsingDir))

                for generator in generators:
                    generator.emit_vs_projects()
                    for projName, slnName in projectMan._cbProjectRoots.items():
                        project = projectMan.get_first_project(projName)
                        generator.emit_sln(slnName, project._cbProjectRefs)
