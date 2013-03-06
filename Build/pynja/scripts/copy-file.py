import shutil
import sys

script, srcPath, dstPath = sys.argv

if __name__ == '__main__':
    # TODO: create hardlink if on same volume
    shutil.copyfile(srcPath, dstPath)
