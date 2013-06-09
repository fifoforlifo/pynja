import os
import pynja
import repo

@pynja.project
class a2(repo.CppProject):
    def emit(self):
        sources = [
            "source/a2_0.cpp",
        ]

        with self.make_pch("source/a2_pch.h") as pchTask:
            pass
        self.pchPath = pchTask.outputPath

        with self.cpp_compile(sources) as tasks:
            tasks.usePCH = self.pchPath

        with self.make_static_lib("a2") as task:
            pass

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
