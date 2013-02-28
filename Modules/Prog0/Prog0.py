import pynja
import upynja


@pynja.build.project
class Prog0(upynja.cpp.CppProject):
    def emit(self):
        libA0 = self.projectMan.get_project('A0', self.variant)
        libA1 = self.projectMan.get_project('A1', self.variant)

        # compile one file at a time with per-file settings
        with self.cpp_compile_one("Source/e0_0.cpp") as task:
            task.includePaths.append(upynja.rootPaths.A0 + "/IncludeSpecial")
        with self.cpp_compile_one("Source/e0_7.cpp") as task:
            # force no optimizations on this file
            task.optimize = 0

        # compile multiple files at a time
        sources = [
            "Source/e0_6.cpp",
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
            # broadcast write
            tasks.warnLevel = 1

        # add libraries last
        self.add_input_lib(libA0.libraryPath)
        self.add_input_lib(libA1.libraryPath)

        with self.make_executable("prog0") as task:
            pass

        self.copy(self.outputPath, self.outputPath + ".copy")

    # set c++ compile options that are common to all files in the project
    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(upynja.rootPaths.A0 + "/Include")
        task.includePaths.append(upynja.rootPaths.A1 + "/Include")

