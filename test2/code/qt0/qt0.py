import os
import pynja
import repo

@pynja.project
class qt0(repo.CppProject):
    def emit(self):
        self.includePaths.append(pynja.rootPaths.boost150)
        self.includePaths.extend(self.qtIncludePaths)
        self.includePaths.append(os.path.join(pynja.rootPaths.qt0, "include"))
        self.includePaths.append(os.path.join(pynja.rootPaths.qt0, "source"))
        self.defines.append("FOO")

        # minor optimization: put non-qt code first, so that they're not
        # affected by implicit header dependencies from qt generators
        self.cpp_compile("source/non_qt_code.cpp")
        self.re2c_cpp_compile(["source/lexer.re2c"])

        ui_sources = [
            "source/main_window.ui",
        ]
        self.qt_uic(ui_sources)

        moc_inputs = [
            "include/qbaz.h",
            "source/qfizzle.h",
            "source/qt0.cpp",
        ]
        self.qt_moc_cpp_compile(moc_inputs)

        sources = [
            "source/qt0.cpp",
            "source/qfizzle.cpp",
            "source/qbaz.cpp"
        ]
        self.cpp_compile(sources)
        self.add_cpplib_dependency("qt_xml", "dyn")
        self.add_boost_lib_dependency("thread")
        self.add_boost_lib_dependency("chrono")
        self.add_boost_lib_dependency("system")
        self.make_executable("qt0")
