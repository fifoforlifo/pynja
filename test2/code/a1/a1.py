import os
import pynja
import repo

@pynja.project
class a1(repo.CppProject):
    def emit(self):
        self.add_cpplib_dependency("a2")

        self.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
        self.includePaths.append(os.path.join(repo.rootPaths.a1, "include"))

        sources = [
            "source/a1_0.cpp",
            "source/a1_1.cpp",
            "source/a1_2.cpp",
            "source/a1_3.cpp",
        ]

        self.cpp_compile(sources)
        self.make_library("a1")

