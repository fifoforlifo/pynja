import os
import pynja
import repo

@pynja.project
class a0(repo.CppProject):
    def emit(self):
        libA2 = self.projectMan.get_project('a2', self.variant)

        proto_defs = [
            "source/address.proto",
            "source/person.proto"
        ]
        self.proto_sources = []
        self.proto_sources = self.protoc_cpp_compile(proto_defs)

        sources = [
            "source/a0_0.cpp",
            "source/a0_1.cpp",
            "source/a0_2.cpp",
            "source/a0_3.cpp",
        ]

        with self.make_pch("source/a0_pch.h") as pchTask:
            pchTask.usePCH = libA2.pchPath
            pass

        with self.cpp_compile(sources) as tasks:
            tasks.usePCH = pchTask.outputPath
            for task in tasks:
                task.defines.append("FOO")

        self.add_input_libs(libA2.linkLibraries)

        with self.make_static_lib("a0") as task:
            pass

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
        task.includePaths.append(os.path.join(repo.rootPaths.a0, "include"))
        # add google protobuf directory
        task.includePaths.append(os.path.join(self.builtDir, "source"))
        # add directory for generated headers from proto files
        task.includePaths.append(os.path.join(repo.rootPaths.protobuf, "src"))
        if "msvc" in self.variant.toolchain:
            task.defines.append("_CRT_SECURE_NO_WARNINGS")
            task.defines.append("_SCL_SECURE_NO_WARNINGS")
        task.extraDeps.extend(self.proto_sources)
