from . import io

def write_rsp_file(project, task, options, rspPath = None, joinStr = " \n"):
    rspContents = joinStr.join(options)
    if not rspPath:
        rspPath = task.outputPath + ".rsp"
    io.write_file_if_different(rspPath, rspContents)

    project.makeFiles.append(rspPath)
