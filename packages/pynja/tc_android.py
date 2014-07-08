from .tc_gcc import *

class AndroidGccToolChain(GccToolChain):
    def __init__(self, name, ndkDir, gccVersionStr, platformVer, archStr, prefix = "", suffix = ""):
        # TODO: non-windows host platform
        hostPlatform = 'windows'

        installDir = os.path.join(ndkDir, 'toolchains', prefix + gccVersionStr, 'prebuilt', hostPlatform)
        super().__init__(name, installDir, False, prefix, suffix)
        self.ndkDir = ndkDir
        self.gccVersionStr = gccVersionStr
        self.platformVer = platformVer
        self.archStr = archStr

        shortArch = "arm" if "arm" in archStr else archStr
        sysroot = "%s/platforms/android-%d/arch-%s" % (binutils_esc_path(ndkDir), platformVer, shortArch)
        def _append_sysroot_options(options):
            options.append('-B="%s"' % (binutils_esc_path(installDir)))
            options.append('--sysroot="%s"' % (sysroot))

        # default options (c++)
        _append_sysroot_options(self.defaultCppOptions)

        # default options (link)
        _append_sysroot_options(self.defaultLinkOptions)
        self.defaultLinkOptions.append('-Wl,-L"%s/usr/lib"' % (sysroot))

    def set_cpp_options_libstdcpp(self, task):
        task.includePaths.append('%s/sources/cxx-stl/gnu-libstdc++/%s/include' % (binutils_esc_path(self.ndkDir), self.gccVersionStr))
        task.includePaths.append('%s/sources/cxx-stl/gnu-libstdc++/%s/libs/%s/include' % (binutils_esc_path(self.ndkDir), self.gccVersionStr, self.archStr))

    def set_link_options_libstdcpp(self, task):
        task.extraOptions.append('-Wl,-L"%s/sources/cxx-stl/gnu-libstdc++/%s/libs"' % (binutils_esc_path(self.ndkDir), self.gccVersionStr))

