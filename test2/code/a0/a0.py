import os
import pynja
import repo

@pynja.project
class a0(repo.CppProject):
    def emit(self):
        proto_defs = [
            "source/address.proto",
            "source/person.proto"
        ]
        self.proto_sources = []
        proto_sources = []
        with self.protoc(proto_defs, 'cpp') as tasks:
            for task in tasks:
                proto_sources.append(task.outputPath)
                with self.cpp_compile_one(task.outputPath) as cppTask:
                    pass
        self.proto_sources = proto_sources

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
        # add google protobuf directory
        task.includePaths.append(os.path.join(self.builtDir, "source"))
        # add directory for generated headers from proto files
        task.includePaths.append(os.path.join(repo.rootPaths.protobuf, "src"))
        if "msvc" in self.variant.toolchain:
            task.defines.append("_CRT_SECURE_NO_WARNINGS")
            task.defines.append("_SCL_SECURE_NO_WARNINGS")
        task.extraDeps.extend(self.proto_sources)
