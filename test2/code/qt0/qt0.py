import os
import pynja
import repo

@pynja.project
class qt0(repo.CppProject):
    def emit(self):
        # minor optimization: put non-qt code first, so that they're not
        # affected by implicit header dependencies from qt generators
        self.cpp_compile("source/non_qt_code.cpp")

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
        self.add_lib_dependency(self.get_project("qt_xml", self.variant))
        self.make_executable("qt0")

    # set c++ compile options that are common to all files in the project
    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        self.set_pp_options(task)

    def set_qt_moc_options(self, task):
        super().set_qt_moc_options(task)
        self.set_pp_options(task)

    # helper function to set include paths and defines
    def set_pp_options(self, task):
        task.includePaths.extend(self.qtIncludePaths)
        task.includePaths.append(os.path.join(repo.rootPaths.qt0, "include"))
        task.includePaths.append(os.path.join(repo.rootPaths.qt0, "source"))
