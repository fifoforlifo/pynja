import shutil
import sys

script, srcPath, dstPath = sys.argv

if __name__ == '__main__':
    shutil.copyfile(srcPath, dstPath)
