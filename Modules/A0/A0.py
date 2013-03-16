import pynja
import repo

@pynja.project
class A0(repo.CppProject):
    def emit(self):
        sources = [
            "Source/a0_0.cpp",
            "Source/a0_1.cpp",
            "Source/a0_2.cpp",
            "Source/a0_3.cpp",
        ]

        with self.make_pch("Source/a0_pch.h") as pchTask:
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
