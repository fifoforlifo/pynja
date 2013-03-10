import pynja
import upynja

@pynja.build.project
class A0(upynja.cpp.CppProject):
    def emit(self):
        sources = [
            "Source/a0_0.cpp",
            "Source/a0_1.cpp",
            "Source/a0_2.cpp",
            "Source/a0_3.cpp",
        ]

        with self.make_pch("Source/a0_pch.cpp") as pchTask:
            pass

        with self.cpp_compile(sources) as tasks:
            tasks.usePCH = pchTask.outputPath

        with self.make_static_lib("a0") as task:
            pass
