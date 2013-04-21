import os
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
        proto_sources = [
            "source/address.proto",
            "source/person.proto"
        ]

        with self.make_pch("source/a0_pch.h") as pchTask:
            pass

        with self.protoc(proto_sources, 'cpp') as tasks:
            for task in tasks:
                with self.cpp_compile_one(task.outputPath) as cppTask:
                    cppTask.includePaths.append(os.path.join(repo.rootPaths.protobuf, "src"))

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
            task.defines.append("_SCL_SECURE_NO_WARNINGS")
