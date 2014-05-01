import os
import pynja
import repo

@pynja.project
class a2(repo.CppProject):
    def emit(self):
        self.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))

        sources = [
            "source/a2_0.cpp",
        ]

        pchTask = self.make_pch("source/a2_pch.h")
        with self.cpp_compile_ex(sources) as tasks:
            tasks.usePCH = pchTask.outputPath

        self.make_library("a2")

@pynja.project
class a2_client(repo.CppProject):
    def emit(self):
        libA2 = self.add_cpplib_dependency('a2')
        pchTask = self.make_pch("source/a2_client_pch.h")
        # export a2_client's pchPath for other projects to use
        self.pchPath = pchTask.outputPath

        # allow a2_client to be a frontend for a2
        self.propagate_lib_dependencies()

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
