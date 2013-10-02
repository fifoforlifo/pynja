import os
import pynja
import repo

@pynja.project
class a2_client(repo.CppProject):
    def emit(self):
        libA2 = self.add_cpplib_dependency('a2')
        pchTask = self.make_pch("source/a2_client_pch.h")
        # export a2_client's pchPath for other projects to use
        self.pchPath = pchTask.outputPath

        # allow a2_client to be a frontend for a2
        self.propagate_lib_dependencies()

    def set_cpp_compile_options(self, task):
        super().set_cpp_compile_options(task)
        task.includePaths.append(os.path.join(repo.rootPaths.a2, "include"))
