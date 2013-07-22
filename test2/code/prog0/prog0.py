import os
import pynja
import repo


@pynja.project
class prog0(repo.CppProject):
    def emit(self):
        libA0 = self.get_project('a0', self.variant)
        libA1 = self.get_project('a1', self.variant)
        # add library dependencies in link order (they will be added to the end of the linker cmdline)
        self.add_lib_dependency(libA0)
        self.add_lib_dependency(libA1)

        # compile one file at a time with per-file settings
        with self.cpp_compile_one("source/e0_0.cpp") as task:
            task.includePaths.append(os.path.join(repo.rootPaths.a0, "includeSpecial"))
        with self.cpp_compile_one("source/e0_7.cpp") as task:
            # force no optimizations on this file
            task.optimize = 0

        # compile multiple files at a time
        sources = [
            "source/e0_6.cpp",
            "source/e0_1.cpp",
            "source/e0_2.cpp",
        ]
        with self.cpp_compile(sources) as tasks:
            pass

        # compile multiple files at a time, with same custom per-file settings
        # on each file in the list
        sloppyFiles = [
            "source/e0_3.cpp",
            "source/e0_4.cpp",
            "source/e0_5.cpp",
        ]
        with self.cpp_compile(sloppyFiles) as tasks:
            for task in tasks:
                task.warnLevel = 1

        sloppyFiles_b = [
            "source/e0_3b.cpp",
            "source/e0_4b.cpp",
            "source/e0_5b.cpp",
        ]
        with self.cpp_compile(sloppyFiles_b) as tasks:
            # broadcast write
            tasks.warnLevel = 1

        with self.make_executable("prog0") as task:
            pass

        self.copy(self.outputPath, self.outputPath + ".copy")

    # set c++ compile options that are common to all files in the project
    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(os.path.join(repo.rootPaths.a0, "include"))
        task.includePaths.append(os.path.join(repo.rootPaths.a1, "include"))

