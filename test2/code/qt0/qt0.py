import os
import pynja
import repo


@pynja.project
class qt0(repo.CppProject):
    def emit(self):
        ui_sources = [
            "source/main_window.ui",
        ]
        self.qt_uic(ui_sources)

        moc_headers = [
            "include/qbaz.h",
            "source/qfizzle.h",
        ]
        self.qt_moc_cpp_compile(moc_headers)

        sources = [
            "source/qt0.cpp",
            "source/qfizzle.cpp",
            "source/qbaz.cpp"
        ]
        self.cpp_compile(sources)
        self.qt_add_lib_dependency("Core")
        self.make_executable("qt0")

    # set c++ compile options that are common to all files in the project
    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.extend(self.qtIncludePaths)
        task.includePaths.append(os.path.join(repo.rootPaths.qt0, "include"))
        task.includePaths.append(os.path.join(repo.rootPaths.qt0, "source"))
