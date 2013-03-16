# This file is intentionally in a directory that is not located in sys.path.
# That causes the python runtime to return an absolute path for __file__.

import os

def get_root_dir():
    absDir = os.path.dirname(__file__)
    rootDir = os.path.normpath(absDir + "../../../..")
    return rootDir
