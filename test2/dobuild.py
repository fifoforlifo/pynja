import os, sys, time

def do_build():
    if not os.path.exists('_out/built/build.ninja'):
        exitcode = os.system('python remake.py')
        if exitcode:
            return exitcode

    args = ''
    for i in range(1, len(sys.argv)):
        args += ' ' + sys.argv[i]
    exitcode = os.system('ninja -C _out/built %s' % (args))
    if exitcode:
        return exitcode

    return 0

if __name__ == '__main__':
    startTime = time.time()
    exitcode = do_build()
    endTime = time.time()

    elapsed = endTime - startTime
    print('build took %.2f seconds' % elapsed)

    exit(exitcode)