import os
import pynja
import repo

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

            self.deploy(productDir)

        else:
            raise Exception("Unsupported product %s" % self.variant.product)
