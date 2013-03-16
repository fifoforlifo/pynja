from . import build

def write_rsp_file(project, task, options):
    rspContents = ' \n'.join(options)
    rspPath = task.outputPath + ".rsp"
    build.write_file_if_different(rspPath, rspContents)

    project.makeFiles.append(rspPath)
