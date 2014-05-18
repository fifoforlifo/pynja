import os
import pynja
import repo

repo.import_repo_dir('code/a')
repo.import_repo_dir('code/prog0')
repo.import_repo_dir('code/java1')
repo.import_repo_dir('code/java2')
repo.import_repo_dir('code/qt0')

# additional build/source paths
repo.rootPaths.dllexport = os.path.join(repo.rootDir, "code/dllexport")

@pynja.project
class test2(repo.DeployProject):
    def emit(self):
        productDir = os.path.join(repo.rootPaths.bin, str(self.variant))

        if self.variant.product == "app32":
            if os.name == 'nt':
                tools = "msvc11-x86"
            elif os.name == 'posix':
                tools = "gcc-x86"
            else:
                raise Exception("Unsupported OS %s" % os.name)

            primaryVariantStr = "windows-%s-%s-dcrt" % (tools, self.variant.config)
            primaryVariant = repo.CppVariant(primaryVariantStr)
            self.add_runtime_dependency_project(self.get_project('prog0', primaryVariant))

            self.deploy(productDir)

        elif self.variant.product == "app64":
            if os.name == 'nt':
                tools = "msvc11-amd64"
            elif os.name == 'posix':
                tools = "gcc-amd64"
            else:
                raise Exception("Unsupported OS %s" % os.name)

            primaryVariantStr = "windows-%s-%s-dcrt" % (tools, self.variant.config)
            primaryVariant = repo.CppVariant(primaryVariantStr)
            self.add_runtime_dependency_project(self.get_project('prog0', primaryVariant))
            if primaryVariant.toolchain == 'msvc11':
                self.add_runtime_dependency_project(self.get_project('qt0', primaryVariant))

            self.deploy(productDir)

        else:
            raise Exception("Unsupported product %s" % self.variant.product)

        # do this last, to capture referenced projects
        self.projectMan.add_cb_project_root(self)
