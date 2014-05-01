import os
import pynja
import repo

@pynja.project
class a0(repo.CppProject):
    def emit(self):
        a2 = self.add_cpplib_dependency('a2')
        a2_client = self.get_cpplib_project('a2_client')

        self.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
        self.includePaths.append(os.path.join(repo.rootPaths.a0, "include"))
        # add google protobuf directory
        self.includePaths.append(os.path.join(self.builtDir, "source"))
        # add directory for generated headers from proto files
        self.includePaths.append(os.path.join(repo.rootPaths.protobuf, "src"))
        if "msvc" in self.variant.toolchain:
            self.defines.append("_CRT_SECURE_NO_WARNINGS")
            self.defines.append("_SCL_SECURE_NO_WARNINGS")

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

        with self.make_pch_ex("source/a0_pch.h") as pchTask:
            pchTask.usePCH = a2_client.pchPath

        with self.cpp_compile_ex(sources) as tasks:
            tasks.usePCH = pchTask.outputPath
            for task in tasks:
                task.defines.append("FOO")

        self.make_library("a0")
