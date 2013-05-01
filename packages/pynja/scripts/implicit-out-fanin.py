import sys

script, listFilePath, faninPath, faninDepsPath = sys.argv

def shell_escape_path(path):
    return path.replace(" ", "\\ ")

def generate_fanin_files():
    with open(listFilePath, "rt") as listFile:
        pathList = listFile.readlines()
        with open(faninDepsPath, "wt") as faninDepsFile:
            faninDepsFile.write("%s: \\\n" % shell_escape_path(faninPath))
            for path in pathList:
                faninDepsFile.write("%s \\\n" % shell_escape_path(path))

    with open(faninPath, "wt") as faninFile:
        faninFile.write("1")

if __name__ == '__main__':
    generate_fanin_files()
