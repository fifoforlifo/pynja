import os
import sys

script, listFilePath, faninPath, faninDepsPath = sys.argv

def escape_path(path):
    return path.replace(" ", "\\ ").replace("$", "\\$")

def generate_fanin_files():
    if os.path.exists(faninPath):
        os.unlink(faninPath)
    # do not unlink the faninDeps file, so that upon error it remains dirty

    with open(listFilePath, "rt") as listFile:
        pathList = [path.rstrip() for path in listFile.readlines()]

    for path in pathList:
        if not os.path.exists(path):
            # TODO: this is a hack until we can plumb the real command back to here
            print("error: dependency not found: %s" % path)
            print("Please re-run build.")
            os.unlink(listFilePath)
            sys.exit(1)

    with open(faninDepsPath, "wt") as faninDepsFile:
        faninDepsFile.write("%s: \\\n" % escape_path(faninPath))
        for path in pathList:
            faninDepsFile.write("%s \\\n" % escape_path(path))

    with open(faninPath, "wt") as faninFile:
        faninFile.write("1")

if __name__ == '__main__':
    generate_fanin_files()
