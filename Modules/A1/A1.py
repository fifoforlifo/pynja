import pynja
import repo

@pynja.project
class A1(repo.CppProject):
    def emit(self):
        sources = [
            "Source/a1_0.cpp",
            "Source/a1_1.cpp",
            "Source/a1_2.cpp",
            "Source/a1_3.cpp",
        ]

        with self.cpp_compile(sources) as tasks:
            pass

        with self.make_shared_lib("a1") as task:
            pass
