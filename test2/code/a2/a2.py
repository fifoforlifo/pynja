import os
import pynja
import repo

@pynja.project
class a2(repo.CppProject):
    def emit(self):
        sources = [
            "source/a2_0.cpp",
        ]

        pchTask = self.make_pch("source/a2_pch.h")
        self.pchPath = pchTask.outputPath # export a2's pchPath for other projects to use
        with self.cpp_compile_ex(sources) as tasks:
            tasks.usePCH = pchTask.outputPath

        self.make_static_lib("a2")

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
