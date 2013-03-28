import pynja
import repo

@pynja.project
class a0(repo.CppProject):
    def emit(self):
        sources = [
            "source/a0_0.cpp",
            "source/a0_1.cpp",
            "source/a0_2.cpp",
            "source/a0_3.cpp",
        ]

        with self.make_pch("source/a0_pch.h") as pchTask:
            pass

        with self.cpp_compile(sources) as tasks:
            tasks.usePCH = pchTask.outputPath
            for task in tasks:
                task.defines.append("FOO")

        with self.make_static_lib("a0") as task:
            pass

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        if "msvc" in self.variant.toolchain:
            task.defines.append("_CRT_SECURE_NO_WARNINGS")
