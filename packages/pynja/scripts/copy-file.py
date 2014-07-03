import shutil
import sys

if __name__ == '__main__':
    script, srcPath, dstPath = sys.argv

    shutil.copyfile(srcPath, dstPath)
