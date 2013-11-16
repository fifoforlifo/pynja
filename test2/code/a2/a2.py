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
