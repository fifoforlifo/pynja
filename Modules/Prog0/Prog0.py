import pynja
import upynja

@pynja.build.project
class Prog0(upynja.cpp.CppProject):
    def emit(self):
        libA0 = self.projectMan.getProject('A0', self.variant)
        libA1 = self.projectMan.getProject('A1', self.variant)

        # compile multiple files at a time
        sources = [
            "Source/e0_0.cpp",
            "Source/e0_1.cpp",
            "Source/e0_2.cpp",
        ]
        with self.cpp_compile(sources) as tasks:
            pass

        # compile multiple files at a time, with same custom per-file settings
        # on each file in the list
        sloppyFiles = [
            "Source/e0_3.cpp",
            "Source/e0_4.cpp",
            "Source/e0_5.cpp",
        ]
        with self.cpp_compile(sloppyFiles) as tasks:
            for task in tasks:
                task.warnLevel = 1

        sloppyFiles_b = [
            "Source/e0_3b.cpp",
            "Source/e0_4b.cpp",
            "Source/e0_5b.cpp",
        ]
        with self.cpp_compile(sloppyFiles_b) as tasks:
            tasks.warnLevel = 1

        # compile one file at a time with per-file settings
        with self.cpp_compile_one("Source/e0_6.cpp") as task:
            # this file reaches into A1 sources rather than respecting interface boundaries
            task.includePaths.append(rootPaths.A1 + "/Source")
        with self.cpp_compile_one("Source/e0_7.cpp") as task:
            # force no optimizations on this file
            task.optimize = 0

        # add libraries last
        self.add_input_library(libA0.libraryFile)
        self.add_input_library(libA1.libraryFile)

        with self.link_executable("prog0") as task:
            pass

        self.copy(self.outputFile, self.outputFile + ".copy")

    def set_compile_options(self, task):
        super().set_compile_options(task)
        task.includePaths.append(rootPaths.Boost)
        task.includePaths.append(rootPaths.A0 + "/Include")
        task.includePaths.append(rootPaths.A1 + "/Include")

