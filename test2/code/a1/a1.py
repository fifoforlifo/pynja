import pynja
import repo

@pynja.project
class a1(repo.CppProject):
    def emit(self):
        sources = [
            "source/a1_0.cpp",
            "source/a1_1.cpp",
            "source/a1_2.cpp",
            "source/a1_3.cpp",
        ]

        self.cpp_compile(sources)
        self.make_shared_lib("a1")
