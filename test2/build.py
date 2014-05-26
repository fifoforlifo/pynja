import os, sys

if __name__ == '__main__':
    if not os.path.exists('_out/built/build.ninja'):
        exitcode = os.system('python remake.py')
        if exitcode:
            exit(exitcode)

    args = ''
    for i in range(1, len(sys.argv)):
        args += ' ' + sys.argv[i]
    exitcode = os.system('ninja -C _out/built %s' % (args))
    if exitcode:
        exit(exitcode)
